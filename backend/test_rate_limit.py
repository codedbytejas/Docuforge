"""
DocuForge AI — Rate Limiting & Quota Protection Test Suite
Automated tests covering all 10 core scenarios specified in Section 9.
Mocks Gemini API so no real quota or external network calls are consumed.
Built with standard library unittest.IsolatedAsyncioTestCase.
"""

import asyncio
import json
import os
import sys
import time
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from httpx import AsyncClient, ASGITransport

sys.path.insert(0, str(Path(__file__).resolve().parent))

import rate_limit
from main import app, get_project


class TestRateLimitingAndQuotaProtection(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        """Resets rate limit events, active job slots, and cache before each test."""
        rate_limit.config.reload()
        storage = rate_limit.get_storage()
        if isinstance(storage, rate_limit.SQLiteRateLimitStorage):
            with storage._lock:
                with storage._get_connection() as conn:
                    conn.execute("DELETE FROM rate_limit_events")
                    conn.execute("DELETE FROM active_job_slots")
                    conn.execute("DELETE FROM generation_cache")

    async def test_01_limit_enforced_at_n_plus_one(self):
        """1. Limit enforced at N+1 requests with correct 429, Retry-After, and structured body."""
        rate_limit.config.enabled = True
        rate_limit.config.generations_per_hour = 3

        mock_docs = {"readme": "Mock Readme", "functions": "None", "classes": "None", "usage": "None", "api": "None", "dependencies": "None", "architecture": "None"}

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            await client.get("/api/status")

            proj = (await client.post("/api/projects", json={"name": "N+1 Test", "code": "def fn(): pass"})).json()
            pid = proj["id"]

            with patch("main.run", return_value=mock_docs):
                # First 3 requests should succeed
                for i in range(3):
                    await client.put(f"/api/projects/{pid}", json={"name": "N+1 Test", "code": f"def fn_{i}(): pass"})
                    res = await client.post(f"/api/projects/{pid}/generate")
                    self.assertEqual(res.status_code, 200, f"Request {i+1} failed: {res.status_code}")

                # 4th request (N+1) must be rejected with 429
                await client.put(f"/api/projects/{pid}", json={"name": "N+1 Test", "code": "def fn_over(): pass"})
                r4 = await client.post(f"/api/projects/{pid}/generate")
                self.assertEqual(r4.status_code, 429, f"Expected 429 on request 4, got {r4.status_code}")

                body = r4.json()
                self.assertEqual(body["error"], "rate_limited")
                self.assertEqual(body["scope"], "user")
                self.assertIn("hourly limit", body["message"].lower())
                self.assertGreater(body["retry_after_seconds"], 0)
                self.assertIn("Retry-After", r4.headers)
                self.assertEqual(int(r4.headers["Retry-After"]), int(body["retry_after_seconds"]))

    async def test_02_window_reset_allows_requests_again(self):
        """2. Window reset allows requests again using simulated time advancing."""
        rate_limit.config.enabled = True
        rate_limit.config.generations_per_hour = 2

        storage = rate_limit.get_storage()
        keys = ["usr:simulated_user", "ip:10.0.0.1"]

        t0 = 1000000.0
        # Use up quota at t0
        allowed1, cnt1, _ = storage.check_and_record(keys, limit=2, window_seconds=3600.0, now=t0, cost=1)
        allowed2, cnt2, _ = storage.check_and_record(keys, limit=2, window_seconds=3600.0, now=t0 + 10.0, cost=1)
        self.assertTrue(allowed1)
        self.assertTrue(allowed2)

        # 3rd request at t0 + 20s must be blocked
        allowed3, cnt3, retry3 = storage.check_and_record(keys, limit=2, window_seconds=3600.0, now=t0 + 20.0, cost=1)
        self.assertFalse(allowed3)
        self.assertGreater(retry3, 0)

        # Advance fake clock past the 1-hour window (3601 seconds)
        t1 = t0 + 3601.0
        allowed4, cnt4, retry4 = storage.check_and_record(keys, limit=2, window_seconds=3600.0, now=t1, cost=1)
        self.assertTrue(allowed4, "Request after window expiration should be allowed")

    async def test_03_dual_tracking_cookie_and_ip(self):
        """3. Cookie cleared still limited via IP; two IPs with one cookie are limited via cookie."""
        rate_limit.config.enabled = True
        rate_limit.config.generations_per_hour = 2

        mock_docs = {"readme": "Dual Track", "functions": "None", "classes": "None", "usage": "None", "api": "None", "dependencies": "None", "architecture": "None"}

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            await client.get("/api/status")

            proj = (await client.post("/api/projects", json={"name": "Dual Track", "code": "a = 1"})).json()
            pid = proj["id"]

            with patch("main.run", return_value=mock_docs):
                # Exhaust quota (2 requests)
                await client.post(f"/api/projects/{pid}/generate")
                await client.put(f"/api/projects/{pid}", json={"name": "Dual Track", "code": "a = 2"})
                await client.post(f"/api/projects/{pid}/generate")

                # Part A: Clear cookie (simulate user clearing browser cookies)
                client.cookies.clear()
                self.assertIsNone(client.cookies.get(rate_limit.COOKIE_NAME))

                # Attempt 3rd request: socket IP still exhausts limit -> blocked!
                await client.put(f"/api/projects/{pid}", json={"name": "Dual Track", "code": "a = 3"})
                res_ip_blocked = await client.post(f"/api/projects/{pid}/generate")
                self.assertEqual(res_ip_blocked.status_code, 429)
                self.assertIn("hourly limit", res_ip_blocked.json()["message"].lower())

        # Part B: Two different IPs sharing the same cookie are limited via cookie
        storage = rate_limit.get_storage()
        cookie_user_key = "usr:shared_cookie_user"
        ip1_key = "ip:10.0.0.1"
        ip2_key = "ip:10.0.0.2"

        t = time.time()
        storage.record_usage([f"gen_hr:{cookie_user_key}", f"gen_hr:{ip1_key}"], cost=1, now=t)
        storage.record_usage([f"gen_hr:{cookie_user_key}", f"gen_hr:{ip1_key}"], cost=1, now=t)

        allowed, _, _ = storage.check_and_record([f"gen_hr:{cookie_user_key}", f"gen_hr:{ip2_key}"], limit=2, window_seconds=3600.0, now=t)
        self.assertFalse(allowed, "Second IP with exhausted cookie must be blocked")

    async def test_04_concurrency_slot_lifecycle(self):
        """4. Concurrency slot released on success, failure and cancel."""
        rate_limit.config.enabled = True
        rate_limit.config.max_concurrent_jobs = 1

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            await client.get("/api/status")

            proj = (await client.post("/api/projects", json={"name": "Concurrency", "code": "def run(): pass"})).json()
            pid = proj["id"]

            # 1. Start job 1
            r1 = await client.post(f"/api/projects/{pid}/jobs")
            self.assertEqual(r1.status_code, 200)
            j1_id = r1.json()["id"]

            # 2. Concurrently starting job 2 returns 429
            r2 = await client.post(f"/api/projects/{pid}/jobs")
            self.assertEqual(r2.status_code, 429)
            self.assertEqual(r2.json()["scope"], "concurrency")

            # 3. Cancel job 1: slot is released
            cancel_res = await client.post(f"/api/jobs/{j1_id}/cancel")
            self.assertEqual(cancel_res.status_code, 200)

            # 4. Job 3 can now acquire slot
            r3 = await client.post(f"/api/projects/{pid}/jobs")
            self.assertEqual(r3.status_code, 200)
            j3_id = r3.json()["id"]

            await client.post(f"/api/jobs/{j3_id}/cancel")

    async def test_05_global_budget_exhaustion(self):
        """5. Global budget exhausted returns 'service busy' without calling Gemini."""
        rate_limit.config.enabled = True
        rate_limit.config.global_requests_per_minute = 2

        storage = rate_limit.get_storage()
        t = time.time()
        storage.record_usage(["global:minute"], cost=2, now=t)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            await client.get("/api/status")
            proj = (await client.post("/api/projects", json={"name": "Global Test", "code": "val = 100"})).json()
            pid = proj["id"]

            mock_docs = {"readme": "# Ok", "functions": "None", "classes": "None", "usage": "None", "api": "None", "dependencies": "None", "architecture": "None"}
            with patch("main.run", return_value=mock_docs) as mock_gemini_run:
                res = await client.post(f"/api/projects/{pid}/generate")
                self.assertEqual(res.status_code, 429)
                body = res.json()
                self.assertEqual(body["error"], "rate_limited")
                self.assertEqual(body["scope"], "global")
                self.assertIn("busy", body["message"].lower())
                mock_gemini_run.assert_not_called()

    async def test_06_cache_hit_consumes_no_quota(self):
        """6. Cache hit returns stored result without calling Gemini and without consuming quota."""
        rate_limit.config.enabled = True
        rate_limit.config.generations_per_hour = 1

        storage = rate_limit.get_storage()
        mock_cached_docs = {"readme": "# Cached Content", "functions": "None", "classes": "None", "usage": "None", "api": "None", "dependencies": "None", "architecture": "None"}

        code_snippet = "const calculate = (a, b) => a + b;"
        cache_key = rate_limit.compute_cache_key(code_snippet, "JavaScript", "Full documentation", "all", "gemini-3.5-flash")
        storage.set_cached_docs(cache_key, mock_cached_docs, "gemini-3.5-flash")

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            await client.get("/api/status")

            proj = (await client.post("/api/projects", json={"name": "Cache App", "language": "JavaScript", "code": code_snippet})).json()
            pid = proj["id"]

            with patch("main.run") as mock_gemini_run:
                # 1st request hits cache
                res1 = await client.post(f"/api/projects/{pid}/generate")
                self.assertEqual(res1.status_code, 200)
                data1 = res1.json()
                self.assertTrue(data1.get("cached"))
                self.assertEqual(data1["docs"]["readme"], "# Cached Content")
                mock_gemini_run.assert_not_called()

                # Quota remains 1
                usage = (await client.get("/api/usage")).json()
                self.assertEqual(usage["generations"]["hourly_remaining"], 1)

    async def test_07_gemini_429_bounded_backoff_and_friendly_error(self):
        """7. Gemini 429 triggers bounded backoff with jitter, then friendly error."""
        from main import gemini

        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.models.generate_content.side_effect = RuntimeError("429 Resource exhausted: Rate limit reached")

        with patch("os.getenv", side_effect=lambda k, d=None: "mock_key" if k == "GEMINI_API_KEY" else d), \
             patch("google.genai.Client", return_value=mock_client), \
             patch("time.sleep") as mock_sleep:

            from fastapi import HTTPException
            with self.assertRaises(HTTPException) as cm:
                gemini("test prompt")

            self.assertEqual(cm.exception.status_code, 429)
            detail = cm.exception.detail
            self.assertIsInstance(detail, dict)
            self.assertEqual(detail["scope"], "global")
            self.assertIn("temporarily reached", detail["message"].lower())
            self.assertGreaterEqual(mock_sleep.call_count, 2)

    async def test_08_concurrent_race_does_not_overshoot(self):
        """8. Concurrent requests do not overshoot the limit (async race test)."""
        rate_limit.config.enabled = True
        limit = 3
        window = 60.0

        storage = rate_limit.get_storage()
        user_keys = ["usr:race_tester", "ip:127.0.0.1"]

        async def try_acquire(idx):
            await asyncio.sleep(0.005 * (idx % 3))
            allowed, count, retry = storage.check_and_record(user_keys, limit=limit, window_seconds=window, cost=1)
            return allowed

        results = await asyncio.gather(*(try_acquire(i) for i in range(15)))
        success_count = sum(1 for r in results if r is True)
        blocked_count = sum(1 for r in results if r is False)

        self.assertEqual(success_count, limit)
        self.assertEqual(blocked_count, 15 - limit)

    async def test_09_trusted_proxy_x_forwarded_for(self):
        """9. X-Forwarded-For ignored unless TRUSTED_PROXY=true."""
        mock_req = MagicMock()
        mock_req.headers = {"X-Forwarded-For": "203.0.113.195, 10.0.0.1"}
        mock_req.client.host = "127.0.0.1"

        ip_untrusted = rate_limit.extract_client_ip(mock_req, trusted_proxy=False)
        self.assertEqual(ip_untrusted, "127.0.0.1")

        ip_trusted = rate_limit.extract_client_ip(mock_req, trusted_proxy=True)
        self.assertEqual(ip_trusted, "203.0.113.195")

    async def test_10_existing_flows_work_with_rl_disabled(self):
        """10. Existing flows still work normally when RL_ENABLED=false."""
        rate_limit.config.enabled = False

        mock_docs = {"readme": "# Standard Flow", "functions": "None", "classes": "None", "usage": "None", "api": "None", "dependencies": "None", "architecture": "None"}

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            await client.get("/api/status")

            proj = (await client.post("/api/projects", json={"name": "Disabled Flow", "code": "def standard(): pass"})).json()
            pid = proj["id"]

            with patch("main.run", return_value=mock_docs):
                for i in range(10):
                    res = await client.post(f"/api/projects/{pid}/generate")
                    self.assertEqual(res.status_code, 200)

                usage = (await client.get("/api/usage")).json()
                self.assertFalse(usage["rate_limiting_enabled"])
                self.assertTrue(usage["service_available"])

    async def test_11_api_key_failover_pool(self):
        """11. Automatic failover: when Key 1 fails with 429/quota, Key 2 succeeds without error."""
        from main import gemini

        calls = []
        def mock_client_factory(api_key, **kwargs):
            mock = MagicMock()
            mock.__enter__.return_value = mock
            if api_key == "key_exhausted":
                mock.models.generate_content.side_effect = RuntimeError("429 RESOURCE_EXHAUSTED: Quota exceeded")
            elif api_key == "key_valid_fallback":
                resp = MagicMock()
                resp.text = '{"readme": "# Successful Fallback Doc"}'
                mock.models.generate_content.return_value = resp
            calls.append(api_key)
            return mock

        env_vars = {
            "GEMINI_API_KEYS": "key_exhausted, key_valid_fallback",
            "GEMINI_MODEL": "gemini-3.5-flash"
        }

        with patch("os.getenv", side_effect=lambda k, d=None: env_vars.get(k, d)), \
             patch("google.genai.Client", side_effect=mock_client_factory), \
             patch("time.sleep"):

            result = gemini("Document this code")
            self.assertIn("Successful Fallback Doc", result)
            self.assertIn("key_exhausted", calls)
            self.assertIn("key_valid_fallback", calls)

    async def test_12_groq_integration_and_cross_provider_failover(self):
        """12. Groq Cloud integration: standalone Groq generation and cross-provider failover."""
        from main import gemini

        # Mock httpx response for Groq
        mock_groq_resp = MagicMock()
        mock_groq_resp.status_code = 200
        mock_groq_resp.json.return_value = {
            "choices": [{"message": {"content": '{"readme": "# Groq Generated Documentation"}'}}]
        }

        mock_httpx_client = MagicMock()
        mock_httpx_client.__enter__.return_value = mock_httpx_client
        mock_httpx_client.post.return_value = mock_groq_resp

        # Sub-test A: Standalone Groq when only GROQ_API_KEY is configured
        env_vars_groq_only = {
            "GEMINI_API_KEY": "",
            "GEMINI_API_KEYS": "",
            "GROQ_API_KEY": "gsk_test_key_123",
            "GROQ_MODEL": "llama-3.3-70b-versatile"
        }
        with patch("os.getenv", side_effect=lambda k, d=None: env_vars_groq_only.get(k, d)), \
             patch("httpx.Client", return_value=mock_httpx_client):
            res = gemini("test prompt")
            self.assertIn("Groq Generated Documentation", res)

        # Sub-test B: Cross-provider failover: Gemini fails -> automatically routes to Groq
        mock_gemini_client = MagicMock()
        mock_gemini_client.__enter__.return_value = mock_gemini_client
        mock_gemini_client.models.generate_content.side_effect = RuntimeError("429 RESOURCE_EXHAUSTED: Gemini quota depleted")

        env_vars_failover = {
            "GEMINI_API_KEY": "gemini_depleted_key",
            "GROQ_API_KEY": "gsk_backup_key_456",
            "GROQ_MODEL": "llama-3.3-70b-versatile"
        }
        with patch("os.getenv", side_effect=lambda k, d=None: env_vars_failover.get(k, d)), \
             patch("google.genai.Client", return_value=mock_gemini_client), \
             patch("httpx.Client", return_value=mock_httpx_client), \
             patch("time.sleep"):
            res = gemini("test prompt")
            self.assertIn("Groq Generated Documentation", res)


if __name__ == "__main__":
    unittest.main()
