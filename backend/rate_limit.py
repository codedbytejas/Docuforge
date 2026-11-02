"""
DocuForge AI — Rate Limiting, Identity & Quota Protection Module
Provides dual-key identity tracking (Signed Cookie + IP), swappable sliding-window storage,
concurrency slot guards, global rate limits, exponential backoff, and generation caching.
"""

import abc
import hashlib
import hmac
import json
import logging
import math
import os
import re
import secrets
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from fastapi import Request, Response, HTTPException

logger = logging.getLogger("docuforge.ratelimit")

ROOT = Path(__file__).resolve().parent
DB_PATH = Path(os.getenv("DB_PATH", str(ROOT / "docuforge.db")))

# ---------------------------------------------------------------------------
# Configuration Helpers
# ---------------------------------------------------------------------------

def get_env_bool(name: str, default: bool) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in ("true", "1", "yes", "on")

def get_env_int(name: str, default: int) -> int:
    val = os.getenv(name)
    if val is None:
        return default
    try:
        return int(val.strip())
    except ValueError:
        return default

class RateLimitConfig:
    """Dynamic configuration reading from environment variables with documented defaults."""
    def __init__(self):
        self.reload()

    def reload(self):
        self.enabled: bool = get_env_bool("RL_ENABLED", True)
        self.generations_per_hour: int = get_env_int("RL_GENERATIONS_PER_HOUR", 5)
        self.generations_per_day: int = get_env_int("RL_GENERATIONS_PER_DAY", 15)
        self.regenerations_per_hour: int = get_env_int("RL_REGENERATIONS_PER_HOUR", 15)
        self.max_concurrent_jobs: int = get_env_int("RL_MAX_CONCURRENT_JOBS_PER_USER", 1)
        self.global_requests_per_minute: int = get_env_int("RL_GLOBAL_REQUESTS_PER_MINUTE", 15)
        self.global_daily_requests: int = get_env_int("RL_GLOBAL_DAILY_REQUESTS", 1500)
        self.uploads_per_minute: int = get_env_int("RL_UPLOADS_PER_MINUTE", 10)
        self.max_input_chars: int = get_env_int("RL_MAX_INPUT_CHARS", 150_000)
        self.trusted_proxy: bool = get_env_bool("TRUSTED_PROXY", False)
        
        # Secret key for HMAC client cookie signing
        secret = os.getenv("RL_SECRET_KEY")
        if not secret:
            secret = os.getenv("GEMINI_API_KEY", "docuforge-secure-client-salt-default-key")
        self.secret_key: bytes = secret.encode("utf-8")

config = RateLimitConfig()

# ---------------------------------------------------------------------------
# 1. Identity Management: Signed HttpOnly Anonymous Cookie + Client IP
# ---------------------------------------------------------------------------

COOKIE_NAME = "df_client_id"
COOKIE_MAX_AGE = 365 * 24 * 3600  # 1 year

def sign_client_id(client_id: str, secret: Union[bytes, str]) -> str:
    sec_bytes = secret if isinstance(secret, bytes) else secret.encode("utf-8")
    sig = hmac.new(sec_bytes, client_id.encode("utf-8"), hashlib.sha256).hexdigest()[:16]
    return f"{client_id}.{sig}"

def verify_and_extract_client_id(cookie_val: Optional[str], secret: Union[bytes, str]) -> Optional[str]:
    if not cookie_val or "." not in cookie_val:
        return None
    client_id, sig = cookie_val.split(".", 1)
    sec_bytes = secret if isinstance(secret, bytes) else secret.encode("utf-8")
    expected = hmac.new(sec_bytes, client_id.encode("utf-8"), hashlib.sha256).hexdigest()[:16]
    if hmac.compare_digest(sig, expected):
        return client_id
    return None

class ClientIdentity:
    def __init__(self, client_id: str, client_ip: str, is_new_cookie: bool = False):
        self.client_id = client_id
        self.client_ip = client_ip
        self.is_new_cookie = is_new_cookie

    @property
    def user_key(self) -> str:
        return f"usr:{self.client_id}"

    @property
    def ip_key(self) -> str:
        return f"ip:{self.client_ip}"

    def get_dual_keys(self) -> List[str]:
        """Dual-tracking: Count against BOTH the cookie id and the IP."""
        return [self.user_key, self.ip_key]

    def anonymized_id(self) -> str:
        """Safe identifier for audit logs without exposing raw IP."""
        masked_ip = ".".join(self.client_ip.split(".")[:2] + ["x", "x"]) if "." in self.client_ip else "ip:anon"
        return f"{self.client_id[:8]}@{masked_ip}"

def extract_client_ip(request: Request, trusted_proxy: bool) -> str:
    """
    Extracts the client IP.
    When TRUSTED_PROXY is True, reads client IP from X-Forwarded-For (leftmost client address).
    Otherwise, strictly uses the socket connection address request.client.host.
    Never trusts X-Forwarded-For by default.
    """
    if trusted_proxy:
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            first_ip = forwarded_for.split(",")[0].strip()
            if first_ip:
                return first_ip
    if request.client and request.client.host:
        return request.client.host
    return "127.0.0.1"

def get_client_identity(request: Request) -> ClientIdentity:
    """Identifies the caller via signed HttpOnly cookie combined with client IP."""
    cookie_val = request.cookies.get(COOKIE_NAME)
    client_id = verify_and_extract_client_id(cookie_val, config.secret_key)
    is_new = False

    if not client_id:
        client_id = secrets.token_hex(16)
        is_new = True

    ip = extract_client_ip(request, config.trusted_proxy)
    return ClientIdentity(client_id, ip, is_new_cookie=is_new)

def attach_client_cookie(response: Response, identity: ClientIdentity):
    """Sets signed, HttpOnly client cookie if newly generated."""
    if identity.is_new_cookie:
        signed_val = sign_client_id(identity.client_id, config.secret_key)
        response.set_cookie(
            key=COOKIE_NAME,
            value=signed_val,
            max_age=COOKIE_MAX_AGE,
            httponly=True,
            samesite="lax",
            path="/"
        )

# ---------------------------------------------------------------------------
# 2. Swappable Limiter Storage Interface & SQLite Implementation
# ---------------------------------------------------------------------------

class RateLimitStorage(abc.ABC):
    @abc.abstractmethod
    def check_and_record(
        self,
        keys: List[str],
        limit: int,
        window_seconds: float,
        now: Optional[float] = None,
        cost: int = 1
    ) -> Tuple[bool, int, float]:
        """
        Atomically checks if any key exceeds limit in window_seconds.
        If allowed, records cost for all keys.
        Returns: (allowed: bool, max_count_in_window: int, retry_after_seconds: float)
        """
        pass

    @abc.abstractmethod
    def get_remaining(
        self,
        keys: List[str],
        limit: int,
        window_seconds: float,
        now: Optional[float] = None
    ) -> Tuple[int, float]:
        """Returns (strictest_remaining_count: int, reset_seconds: float)."""
        pass

    @abc.abstractmethod
    def record_usage(
        self,
        keys: List[str],
        cost: int = 1,
        now: Optional[float] = None
    ) -> None:
        """Explicitly records quota consumption (for delayed or real-call accounting)."""
        pass

    @abc.abstractmethod
    def acquire_concurrency_slot(
        self,
        job_id: str,
        user_key: str,
        ip_key: str,
        max_concurrent: int,
        now: Optional[float] = None
    ) -> bool:
        """Acquires a concurrency execution slot if under max_concurrent."""
        pass

    @abc.abstractmethod
    def release_concurrency_slot(self, job_id: str) -> None:
        """Releases the concurrency slot for a job."""
        pass

    @abc.abstractmethod
    def get_active_concurrency_count(self, user_key: str, ip_key: str) -> int:
        """Returns active concurrent jobs for caller."""
        pass

    @abc.abstractmethod
    def get_cached_docs(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Retrieves cached generation result."""
        pass

    @abc.abstractmethod
    def set_cached_docs(self, cache_key: str, docs: Dict[str, Any], model: str) -> None:
        """Stores generation result in cache."""
        pass

    @abc.abstractmethod
    def cleanup(self, older_than: float) -> int:
        """Purges expired event records."""
        pass


class SQLiteRateLimitStorage(RateLimitStorage):
    """
    Production-grade SQLite sliding-window limiter storage with thread locks,
    additive schema, atomic transactions, and query optimizations.
    """
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._lock = threading.Lock()
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._lock:
            with self._get_connection() as conn:
                # Additive rate limit events table (sliding window log)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS rate_limit_events (
                        key TEXT NOT NULL,
                        timestamp REAL NOT NULL,
                        cost INTEGER DEFAULT 1
                    )
                """)
                conn.execute("CREATE INDEX IF NOT EXISTS idx_rl_events_key_ts ON rate_limit_events(key, timestamp)")

                # Additive concurrency slot management table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS active_job_slots (
                        job_id TEXT PRIMARY KEY,
                        user_key TEXT NOT NULL,
                        ip_key TEXT NOT NULL,
                        created_at REAL NOT NULL
                    )
                """)
                conn.execute("CREATE INDEX IF NOT EXISTS idx_active_slots_user ON active_job_slots(user_key)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_active_slots_ip ON active_job_slots(ip_key)")

                # Additive generation cache table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS generation_cache (
                        cache_key TEXT PRIMARY KEY,
                        docs_json TEXT NOT NULL,
                        model TEXT NOT NULL,
                        created_at REAL NOT NULL
                    )
                """)
                conn.execute("CREATE INDEX IF NOT EXISTS idx_gen_cache_key ON generation_cache(cache_key)")

    def check_and_record(
        self,
        keys: List[str],
        limit: int,
        window_seconds: float,
        now: Optional[float] = None,
        cost: int = 1
    ) -> Tuple[bool, int, float]:
        curr_time = now if now is not None else time.time()
        cutoff = curr_time - window_seconds

        with self._lock:
            with self._get_connection() as conn:
                max_count = 0
                max_retry_after = 0.0

                # Check all keys (user and IP). The strictest one governs.
                for k in keys:
                    cur = conn.execute(
                        "SELECT COALESCE(SUM(cost), 0) as cnt, MIN(timestamp) as oldest "
                        "FROM rate_limit_events WHERE key = ? AND timestamp >= ?",
                        (k, cutoff)
                    )
                    row = cur.fetchone()
                    count = int(row["cnt"]) if row and row["cnt"] is not None else 0
                    oldest = row["oldest"] if row and row["oldest"] is not None else None

                    if count > max_count:
                        max_count = count

                    is_blocked = (count >= limit) if cost == 0 else (count + cost > limit)
                    if is_blocked:
                        retry_after = 1.0
                        if oldest is not None:
                            retry_after = max(1.0, math.ceil((oldest + window_seconds) - curr_time))
                        if retry_after > max_retry_after:
                            max_retry_after = retry_after

                if max_retry_after > 0.0:
                    return False, max_count, max_retry_after

                # All keys are within limit; atomically record event for all keys if cost > 0
                if cost > 0:
                    for k in keys:
                        conn.execute(
                            "INSERT INTO rate_limit_events(key, timestamp, cost) VALUES (?, ?, ?)",
                            (k, curr_time, cost)
                        )
                return True, max_count + cost, 0.0

    def get_remaining(
        self,
        keys: List[str],
        limit: int,
        window_seconds: float,
        now: Optional[float] = None
    ) -> Tuple[int, float]:
        curr_time = now if now is not None else time.time()
        cutoff = curr_time - window_seconds

        with self._lock:
            with self._get_connection() as conn:
                max_count = 0
                earliest_reset = 0.0

                for k in keys:
                    cur = conn.execute(
                        "SELECT COALESCE(SUM(cost), 0) as cnt, MIN(timestamp) as oldest "
                        "FROM rate_limit_events WHERE key = ? AND timestamp >= ?",
                        (k, cutoff)
                    )
                    row = cur.fetchone()
                    count = int(row["cnt"]) if row and row["cnt"] is not None else 0
                    oldest = row["oldest"] if row and row["oldest"] is not None else None

                    if count > max_count:
                        max_count = count
                    if oldest is not None:
                        res = max(0.0, (oldest + window_seconds) - curr_time)
                        if res > earliest_reset:
                            earliest_reset = res

                remaining = max(0, limit - max_count)
                return remaining, math.ceil(earliest_reset)

    def record_usage(
        self,
        keys: List[str],
        cost: int = 1,
        now: Optional[float] = None
    ) -> None:
        curr_time = now if now is not None else time.time()
        with self._lock:
            with self._get_connection() as conn:
                for k in keys:
                    conn.execute(
                        "INSERT INTO rate_limit_events(key, timestamp, cost) VALUES (?, ?, ?)",
                        (k, curr_time, cost)
                    )

    def acquire_concurrency_slot(
        self,
        job_id: str,
        user_key: str,
        ip_key: str,
        max_concurrent: int,
        now: Optional[float] = None
    ) -> bool:
        curr_time = now if now is not None else time.time()
        # Stale slots older than 15 minutes are reclaimed automatically
        stale_cutoff = curr_time - 900.0

        with self._lock:
            with self._get_connection() as conn:
                # Clean stale slots
                conn.execute("DELETE FROM active_job_slots WHERE created_at < ?", (stale_cutoff,))

                # Check active slots for caller user_key and ip_key
                cur_user = conn.execute("SELECT COUNT(*) as c FROM active_job_slots WHERE user_key = ?", (user_key,)).fetchone()
                cur_ip = conn.execute("SELECT COUNT(*) as c FROM active_job_slots WHERE ip_key = ?", (ip_key,)).fetchone()
                user_slots = cur_user["c"] if cur_user else 0
                ip_slots = cur_ip["c"] if cur_ip else 0

                if max(user_slots, ip_slots) >= max_concurrent:
                    return False

                conn.execute(
                    "INSERT OR REPLACE INTO active_job_slots(job_id, user_key, ip_key, created_at) VALUES (?, ?, ?, ?)",
                    (job_id, user_key, ip_key, curr_time)
                )
                return True

    def release_concurrency_slot(self, job_id: str) -> None:
        with self._lock:
            with self._get_connection() as conn:
                conn.execute("DELETE FROM active_job_slots WHERE job_id = ?", (job_id,))

    def get_active_concurrency_count(self, user_key: str, ip_key: str) -> int:
        with self._lock:
            with self._get_connection() as conn:
                cur_user = conn.execute("SELECT COUNT(*) as c FROM active_job_slots WHERE user_key = ?", (user_key,)).fetchone()
                cur_ip = conn.execute("SELECT COUNT(*) as c FROM active_job_slots WHERE ip_key = ?", (ip_key,)).fetchone()
                return max(cur_user["c"] if cur_user else 0, cur_ip["c"] if cur_ip else 0)

    def get_cached_docs(self, cache_key: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            with self._get_connection() as conn:
                row = conn.execute("SELECT docs_json FROM generation_cache WHERE cache_key = ?", (cache_key,)).fetchone()
                if row:
                    try:
                        return json.loads(row["docs_json"])
                    except Exception:
                        return None
        return None

    def set_cached_docs(self, cache_key: str, docs: Dict[str, Any], model: str) -> None:
        with self._lock:
            with self._get_connection() as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO generation_cache(cache_key, docs_json, model, created_at) VALUES (?, ?, ?, ?)",
                    (cache_key, json.dumps(docs), model, time.time())
                )

    def cleanup(self, older_than: float) -> int:
        with self._lock:
            with self._get_connection() as conn:
                cur = conn.execute("DELETE FROM rate_limit_events WHERE timestamp < ?", (older_than,))
                conn.execute("DELETE FROM active_job_slots WHERE created_at < ?", (older_than,))
                return cur.rowcount


# Default storage instance (swappable with RedisRateLimitStorage in future)
default_storage: RateLimitStorage = SQLiteRateLimitStorage()

def get_storage() -> RateLimitStorage:
    return default_storage

# ---------------------------------------------------------------------------
# 8. Fail-Safe In-Memory Fallback & Logging
# ---------------------------------------------------------------------------

class InMemoryFallbackStorage(RateLimitStorage):
    """
    Fail-safe fallback when primary storage encounters an I/O error or corruption.
    Enforces conservative in-memory rate limiting to protect API quota.
    """
    def __init__(self):
        self._events: Dict[str, List[float]] = {}
        self._slots: Dict[str, Tuple[str, str, float]] = {}
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def check_and_record(
        self,
        keys: List[str],
        limit: int,
        window_seconds: float,
        now: Optional[float] = None,
        cost: int = 1
    ) -> Tuple[bool, int, float]:
        curr = now if now is not None else time.time()
        cutoff = curr - window_seconds
        with self._lock:
            max_c = 0
            retry = 0.0
            for k in keys:
                ts_list = [t for t in self._events.get(k, []) if t >= cutoff]
                self._events[k] = ts_list
                if len(ts_list) > max_c:
                    max_c = len(ts_list)
                is_blocked = (len(ts_list) >= limit) if cost == 0 else (len(ts_list) + cost > limit)
                if is_blocked:
                    oldest = min(ts_list) if ts_list else curr
                    rem = max(1.0, math.ceil((oldest + window_seconds) - curr))
                    if rem > retry:
                        retry = rem
            if retry > 0.0:
                return False, max_c, retry
            if cost > 0:
                for k in keys:
                    self._events.setdefault(k, []).extend([curr] * cost)
            return True, max_c + cost, 0.0

    def get_remaining(self, keys: List[str], limit: int, window_seconds: float, now: Optional[float] = None) -> Tuple[int, float]:
        curr = now if now is not None else time.time()
        cutoff = curr - window_seconds
        with self._lock:
            max_c = 0
            earliest_reset = 0.0
            for k in keys:
                ts_list = [t for t in self._events.get(k, []) if t >= cutoff]
                if len(ts_list) > max_c:
                    max_c = len(ts_list)
                if ts_list:
                    r = max(0.0, (min(ts_list) + window_seconds) - curr)
                    if r > earliest_reset:
                        earliest_reset = r
            return max(0, limit - max_c), math.ceil(earliest_reset)

    def record_usage(self, keys: List[str], cost: int = 1, now: Optional[float] = None) -> None:
        curr = now if now is not None else time.time()
        with self._lock:
            for k in keys:
                self._events.setdefault(k, []).extend([curr] * cost)

    def acquire_concurrency_slot(self, job_id: str, user_key: str, ip_key: str, max_concurrent: int, now: Optional[float] = None) -> bool:
        curr = now if now is not None else time.time()
        with self._lock:
            # Clean slots older than 15 mins
            self._slots = {jid: v for jid, v in self._slots.items() if v[2] >= curr - 900.0}
            user_c = sum(1 for v in self._slots.values() if v[0] == user_key)
            ip_c = sum(1 for v in self._slots.values() if v[1] == ip_key)
            if max(user_c, ip_c) >= max_concurrent:
                return False
            self._slots[job_id] = (user_key, ip_key, curr)
            return True

    def release_concurrency_slot(self, job_id: str) -> None:
        with self._lock:
            self._slots.pop(job_id, None)

    def get_active_concurrency_count(self, user_key: str, ip_key: str) -> int:
        with self._lock:
            user_c = sum(1 for v in self._slots.values() if v[0] == user_key)
            ip_c = sum(1 for v in self._slots.values() if v[1] == ip_key)
            return max(user_c, ip_c)

    def get_cached_docs(self, cache_key: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            return self._cache.get(cache_key)

    def set_cached_docs(self, cache_key: str, docs: Dict[str, Any], model: str) -> None:
        with self._lock:
            self._cache[cache_key] = docs

    def cleanup(self, older_than: float) -> int:
        with self._lock:
            c = 0
            for k in list(self._events.keys()):
                before = len(self._events[k])
                self._events[k] = [t for t in self._events[k] if t >= older_than]
                c += before - len(self._events[k])
            return c

fallback_storage = InMemoryFallbackStorage()

def safe_storage_op(operation_name: str, op_callable):
    """Executes storage operation with graceful in-memory failover on DB errors."""
    try:
        return op_callable(default_storage)
    except Exception as e:
        logger.error(f"[RATE_LIMIT_STORAGE_ERROR] {operation_name} failed on primary storage: {e}. Falling back to in-memory safe store.")
        return op_callable(fallback_storage)


def log_rate_limit_event(scope: str, anonymized_id: str, endpoint: str, retry_after: float):
    """
    Logs rate limit events without code content or sensitive keys.
    Format: [RATE_LIMIT_HIT] scope=user anonymized=abc12345@192.168.x.x endpoint=/api/projects/1/jobs retry_after=120s
    """
    logger.warning(
        f"[RATE_LIMIT_HIT] scope={scope} id={anonymized_id} endpoint={endpoint} retry_after={int(retry_after)}s"
    )

# ---------------------------------------------------------------------------
# 6. Standardized API Responses & Quota Exceptions
# ---------------------------------------------------------------------------

def raise_rate_limited(scope: str, message: str, retry_after_seconds: float):
    """Raises HTTP 429 with strict payload schema and Retry-After header."""
    sec = max(1, int(math.ceil(retry_after_seconds)))
    raise HTTPException(
        status_code=429,
        detail={
            "error": "rate_limited",
            "message": message,
            "scope": scope,
            "retry_after_seconds": sec
        },
        headers={"Retry-After": str(sec)}
    )

def format_retry_time(seconds: float) -> str:
    """Formats retry timestamp (HH:MM UTC) for friendly user notices."""
    target = time.time() + max(1, seconds)
    return time.strftime("%H:%M UTC", time.gmtime(target))

# ---------------------------------------------------------------------------
# Rate Limiting Logic for Endpoints
# ---------------------------------------------------------------------------

def check_global_limits(now: Optional[float] = None):
    """Checks global Gemini call limits per minute and per day."""
    if not config.enabled:
        return

    # Check global per-minute limit
    allowed_min, _, retry_min = safe_storage_op(
        "check_global_minute",
        lambda s: s.check_and_record(
            keys=["global:minute"],
            limit=config.global_requests_per_minute,
            window_seconds=60.0,
            now=now,
            cost=0 # Check only, real cost recorded when Gemini called
        )
    )
    if not allowed_min:
        msg = f"The service is currently busy under high demand. Please try again at {format_retry_time(retry_min)}."
        log_rate_limit_event("global", "global", "gemini_dispatch", retry_min)
        raise_rate_limited("global", msg, retry_min)

    # Check global daily limit
    allowed_day, _, retry_day = safe_storage_op(
        "check_global_day",
        lambda s: s.check_and_record(
            keys=["global:day"],
            limit=config.global_daily_requests,
            window_seconds=86400.0,
            now=now,
            cost=0
        )
    )
    if not allowed_day:
        msg = f"The service has reached its daily generation capacity. Please try again tomorrow at {format_retry_time(retry_day)}."
        log_rate_limit_event("global", "global", "gemini_dispatch", retry_day)
        raise_rate_limited("global", msg, retry_day)


def check_user_generation_limit(identity: ClientIdentity, now: Optional[float] = None):
    """
    Checks caller's generation limits:
    - Hourly: RL_GENERATIONS_PER_HOUR
    - Daily: RL_GENERATIONS_PER_DAY
    Counts against both user cookie and IP (strictest wins).
    """
    if not config.enabled:
        return

    dual_keys_hourly = [f"gen_hr:{k}" for k in identity.get_dual_keys()]
    allowed_hr, count_hr, retry_hr = safe_storage_op(
        "check_user_gen_hour",
        lambda s: s.check_and_record(
            keys=dual_keys_hourly,
            limit=config.generations_per_hour,
            window_seconds=3600.0,
            now=now,
            cost=0 # Verified upfront, decremented on real execution
        )
    )
    if not allowed_hr:
        minutes = math.ceil(retry_hr / 60.0)
        unit = "minute" if minutes == 1 else "minutes"
        msg = f"You have reached your hourly limit ({config.generations_per_hour} generations). Please try again in {minutes} {unit}."
        log_rate_limit_event("user", identity.anonymized_id(), "generate_job", retry_hr)
        raise_rate_limited("user", msg, retry_hr)

    dual_keys_daily = [f"gen_day:{k}" for k in identity.get_dual_keys()]
    allowed_day, count_day, retry_day = safe_storage_op(
        "check_user_gen_day",
        lambda s: s.check_and_record(
            keys=dual_keys_daily,
            limit=config.generations_per_day,
            window_seconds=86400.0,
            now=now,
            cost=0
        )
    )
    if not allowed_day:
        msg = f"You have reached your daily generation limit ({config.generations_per_day} generations). Please try again tomorrow at {format_retry_time(retry_day)}."
        log_rate_limit_event("user", identity.anonymized_id(), "generate_job", retry_day)
        raise_rate_limited("user", msg, retry_day)


def check_user_regeneration_limit(identity: ClientIdentity, now: Optional[float] = None):
    """Checks caller's section regeneration limits per hour."""
    if not config.enabled:
        return

    dual_keys_regen = [f"regen_hr:{k}" for k in identity.get_dual_keys()]
    allowed, count, retry = safe_storage_op(
        "check_user_regen_hour",
        lambda s: s.check_and_record(
            keys=dual_keys_regen,
            limit=config.regenerations_per_hour,
            window_seconds=3600.0,
            now=now,
            cost=0
        )
    )
    if not allowed:
        minutes = math.ceil(retry / 60.0)
        unit = "minute" if minutes == 1 else "minutes"
        msg = f"You have reached your hourly section regeneration limit ({config.regenerations_per_hour}/hr). Please try again in {minutes} {unit}."
        log_rate_limit_event("user", identity.anonymized_id(), "regenerate_section", retry)
        raise_rate_limited("user", msg, retry)


def check_upload_limit(identity: ClientIdentity, now: Optional[float] = None):
    """Applies sliding window rate limit on file uploads."""
    if not config.enabled:
        return

    dual_keys_upload = [f"upload_min:{k}" for k in identity.get_dual_keys()]
    allowed, count, retry = safe_storage_op(
        "check_upload_limit",
        lambda s: s.check_and_record(
            keys=dual_keys_upload,
            limit=config.uploads_per_minute,
            window_seconds=60.0,
            now=now,
            cost=1
        )
    )
    if not allowed:
        msg = f"Upload frequency limit reached ({config.uploads_per_minute}/min). Please wait {int(retry)} seconds before uploading again."
        log_rate_limit_event("user", identity.anonymized_id(), "upload_files", retry)
        raise_rate_limited("user", msg, retry)


def record_real_generation_quota(identity: ClientIdentity, is_regeneration: bool = False, now: Optional[float] = None):
    """
    Called ONLY when a real Gemini API call is executed.
    Cache hits or rejected requests NEVER call this.
    """
    if not config.enabled:
        return

    curr_time = now if now is not None else time.time()
    user_keys = identity.get_dual_keys()

    if is_regeneration:
        regen_keys = [f"regen_hr:{k}" for k in user_keys]
        safe_storage_op("record_regen", lambda s: s.record_usage(regen_keys, cost=1, now=curr_time))
    else:
        hr_keys = [f"gen_hr:{k}" for k in user_keys]
        day_keys = [f"gen_day:{k}" for k in user_keys]
        safe_storage_op("record_gen_hr", lambda s: s.record_usage(hr_keys, cost=1, now=curr_time))
        safe_storage_op("record_gen_day", lambda s: s.record_usage(day_keys, cost=1, now=curr_time))

    # Record global Gemini consumption
    safe_storage_op("record_global_min", lambda s: s.record_usage(["global:minute"], cost=1, now=curr_time))
    safe_storage_op("record_global_day", lambda s: s.record_usage(["global:day"], cost=1, now=curr_time))


# ---------------------------------------------------------------------------
# 5. Generation Result Hash & Caching
# ---------------------------------------------------------------------------

PROMPT_VERSION = "v1"

def compute_cache_key(code: str, language: str, doc_type: str, section: str, model: str) -> str:
    """Produces SHA-256 hash identifying identical documentation queries."""
    normalized_code = re.sub(r"\s+", " ", code.strip())
    raw = f"{PROMPT_VERSION}:{model}:{language.strip().lower()}:{doc_type.strip().lower()}:{section.strip().lower()}:{normalized_code}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

# ---------------------------------------------------------------------------
# 6. Usage Summary for GET /api/usage
# ---------------------------------------------------------------------------

def get_usage_summary(identity: ClientIdentity, now: Optional[float] = None) -> Dict[str, Any]:
    """
    Returns caller's remaining generations (hour/day), regenerations, reset times,
    concurrency status, and service availability. Never exposes IP or other users' data.
    """
    curr_time = now if now is not None else time.time()
    user_keys = identity.get_dual_keys()

    gen_hr_keys = [f"gen_hr:{k}" for k in user_keys]
    gen_hr_rem, gen_hr_reset = safe_storage_op(
        "get_gen_hr",
        lambda s: s.get_remaining(gen_hr_keys, config.generations_per_hour, 3600.0, curr_time)
    )

    gen_day_keys = [f"gen_day:{k}" for k in user_keys]
    gen_day_rem, gen_day_reset = safe_storage_op(
        "get_gen_day",
        lambda s: s.get_remaining(gen_day_keys, config.generations_per_day, 86400.0, curr_time)
    )

    regen_hr_keys = [f"regen_hr:{k}" for k in user_keys]
    regen_hr_rem, regen_hr_reset = safe_storage_op(
        "get_regen_hr",
        lambda s: s.get_remaining(regen_hr_keys, config.regenerations_per_hour, 3600.0, curr_time)
    )

    active_jobs = safe_storage_op(
        "get_active_jobs",
        lambda s: s.get_active_concurrency_count(identity.user_key, identity.ip_key)
    )

    glob_min_rem, _ = safe_storage_op(
        "get_glob_min",
        lambda s: s.get_remaining(["global:minute"], config.global_requests_per_minute, 60.0, curr_time)
    )
    glob_day_rem, _ = safe_storage_op(
        "get_glob_day",
        lambda s: s.get_remaining(["global:day"], config.global_daily_requests, 86400.0, curr_time)
    )
    global_available = (glob_min_rem > 0 and glob_day_rem > 0)

    return {
        "rate_limiting_enabled": config.enabled,
        "generations": {
            "hourly_remaining": gen_hr_rem if config.enabled else config.generations_per_hour,
            "hourly_limit": config.generations_per_hour,
            "hourly_reset_seconds": gen_hr_reset,
            "daily_remaining": gen_day_rem if config.enabled else config.generations_per_day,
            "daily_limit": config.generations_per_day,
            "daily_reset_seconds": gen_day_reset
        },
        "regenerations": {
            "hourly_remaining": regen_hr_rem if config.enabled else config.regenerations_per_hour,
            "hourly_limit": config.regenerations_per_hour,
            "hourly_reset_seconds": regen_hr_reset
        },
        "concurrency": {
            "active_jobs": active_jobs,
            "max_concurrent": config.max_concurrent_jobs
        },
        "service_available": global_available if config.enabled else True,
        "global_status": "ok" if (global_available or not config.enabled) else "busy"
    }
