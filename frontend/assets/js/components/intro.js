/**
 * DocuForge AI — Cinematic Intro Screen
 * Tied to real backend health check + fonts readiness
 * Features Skip button, Error/Retry state, and sessionStorage guard
 */

import { state, setIntroDone } from '../state.js';
import { api } from '../api.js';
import { icons } from '../icons.js';

export function shouldShowIntro() {
  return sessionStorage.getItem('df_intro_done') !== 'true';
}

export function playIntro(onComplete) {
  // If already completed in this browser session, skip immediately
  if (!shouldShowIntro()) {
    if (onComplete) onComplete();
    return;
  }

  const overlay = document.createElement('div');
  overlay.className = 'df-intro-overlay';
  overlay.id = 'df-intro-screen';

  overlay.innerHTML = `
    <div class="df-intro-glow"></div>
    <button class="df-intro-skip-btn" id="df-intro-skip">Skip Intro &rarr;</button>

    <div class="df-intro-container">
      <div class="df-intro-mark-wrapper">
        <div class="df-intro-ring"></div>
        <div class="df-intro-mark">
          ${icons.mark(34)}
        </div>
      </div>

      <div class="df-intro-wordmark">DOCUFORGE AI</div>
      <div class="df-intro-tagline">Your Code. Clearly Documented.</div>
      <h1 class="df-intro-headline">Every great codebase deserves great documentation.</h1>
      <p class="df-intro-sub">Transform source code into meaningful technical documentation with intelligent AI.</p>

      <div id="df-intro-status-area">
        <div class="df-intro-status-box">
          <span class="df-intro-status-dot" id="df-intro-dot"></span>
          <span id="df-intro-status-label">Initializing system runtime...</span>
        </div>
      </div>
    </div>
  `;

  document.body.appendChild(overlay);

  let dismissed = false;
  const dismiss = () => {
    if (dismissed) return;
    dismissed = true;
    setIntroDone();
    overlay.classList.add('fade-out');
    setTimeout(() => {
      overlay.remove();
      if (onComplete) onComplete();
    }, 420);
  };

  document.getElementById('df-intro-skip').onclick = dismiss;

  // Real initialization sequence
  const startTime = Date.now();
  const minDisplayMs = 1500; // minimum ~1.5 s so animation does not flash

  async function performHealthCheck() {
    const statusLabel = document.getElementById('df-intro-status-label');
    const statusDot = document.getElementById('df-intro-dot');
    const statusArea = document.getElementById('df-intro-status-area');

    try {
      if (statusLabel) statusLabel.textContent = 'Verifying engine & model health...';

      // 1. Wait for document fonts to be ready
      if (document.fonts) {
        await document.fonts.ready;
      }

      // 2. Real backend health check call
      const statusRes = await api.getStatus();
      state.status = statusRes;

      const elapsed = Date.now() - startTime;
      const remaining = Math.max(0, minDisplayMs - elapsed);

      if (statusLabel) statusLabel.textContent = 'DocuForge workspace ready';
      if (statusDot) statusDot.className = 'df-intro-status-dot ok';

      setTimeout(() => {
        dismiss();
      }, remaining);

    } catch (err) {
      console.error('Intro health check failed', err);
      if (statusDot) statusDot.className = 'df-intro-status-dot err';
      if (statusArea) {
        statusArea.innerHTML = `
          <div style="display: flex; flex-direction: column; align-items: center; gap: 12px;">
            <div class="df-intro-status-box" style="border-color: rgba(239, 68, 68, 0.4); background: #1a0f0f; color: #fca5a5;">
              <span class="df-intro-status-dot err"></span>
              <span>Cannot connect to backend: ${err.message || 'Service unreachable'}</span>
            </div>
            <div style="display: flex; gap: 10px;">
              <button class="df-btn df-btn-sm df-btn-primary" id="df-intro-retry">Retry Connection</button>
              <button class="df-btn df-btn-sm df-btn-ghost" id="df-intro-continue">Continue to App &rarr;</button>
            </div>
          </div>
        `;

        document.getElementById('df-intro-retry').onclick = () => {
          statusArea.innerHTML = `
            <div class="df-intro-status-box">
              <span class="df-intro-status-dot" id="df-intro-dot"></span>
              <span id="df-intro-status-label">Retrying connection...</span>
            </div>
          `;
          performHealthCheck();
        };

        document.getElementById('df-intro-continue').onclick = dismiss;
      }
    }
  }

  performHealthCheck();
}

