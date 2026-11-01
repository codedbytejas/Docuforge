/**
 * DocuForge AI — Processing Component (/processing)
 * Real-time Truthful Stage Tracking via SSE with In-flight Timers,
 * Total Elapsed Time Counter, File Scope Details, Cancel Action, and Failure Recovery.
 */

import { state, setActiveJob } from '../state.js';
import { api, showToast } from '../api.js';
import { navigate, renderNavbar } from '../router.js';
import { icons } from '../icons.js';

export async function renderProcessing(container, params) {
  const urlParams = params || new URLSearchParams(window.location.search);
  const jobId = urlParams.get('job_id') || sessionStorage.getItem('df_active_job_id');

  // Navigation Guard: Redirect to playground if no job is active
  if (!jobId) {
    navigate('/playground', true);
    return;
  }

  let project = state.currentProject;
  let jobStartedAt = Date.now();
  let jobEndedAt = null;

  container.innerHTML = `
    ${renderNavbar('/processing')}
    <main class="df-page" style="max-width: 780px;">
      <div style="text-align: center; margin-bottom: 32px;">
        <div style="display: flex; align-items: center; justify-content: center; gap: 12px; margin-bottom: 12px; flex-wrap: wrap;">
          <span class="df-badge df-badge-running" id="df-job-badge">
            ${icons.spinner(12)} Live Generation
          </span>
          <span class="df-badge" id="df-scope-stats" style="background: var(--bg-surface-elevated); display: none;"></span>
          <span class="df-mono df-sub" id="df-elapsed-ticker" style="font-size: var(--fs-xs); display: inline-flex; align-items: center; gap: 4px;">
            ${icons.clock(12)} 0.0 s
          </span>
        </div>
        
        <h1 class="df-title-xl" id="df-job-title" style="margin-bottom: 8px;">Understanding your codebase...</h1>
        <p class="df-lead" id="df-job-sub" style="margin: 0 auto; text-align: center; font-size: 15px;">
          Streaming measured milestones directly from the execution runner.
        </p>

        <!-- Cancel Button during running state -->
        <div id="df-cancel-wrapper" style="margin-top: 14px;">
          <button type="button" class="df-btn df-btn-sm df-btn-ghost" id="df-btn-cancel" style="font-size: 12px; color: var(--text-tertiary);">
            ${icons.close(14)} Cancel Analysis
          </button>
        </div>
      </div>

      <div class="df-card" id="df-stages-card">
        <div id="df-stages-list" style="display: flex; flex-direction: column; gap: 14px;">
          <div style="text-align: center; padding: 24px; color: var(--text-secondary);">
            <span class="df-mono">${icons.spinner(16)} Connecting to execution runner...</span>
          </div>
        </div>
      </div>

      <!-- Specific Error / Cancellation Panel -->
      <div id="df-error-panel" style="display: none; margin-top: 24px;">
        <div class="df-banner df-banner-err" style="margin-bottom: 0;">
          <span style="color: var(--status-err);">${icons.alert(20)}</span>
          <div style="flex: 1;">
            <b style="font-size: var(--fs-base); color: var(--status-err);" id="df-error-headline">Generation encountered an error</b>
            <div id="df-error-text" class="df-sub" style="margin: 6px 0 16px; color: var(--text-primary); line-height: 1.5;"></div>
            <div style="display: flex; gap: 10px; flex-wrap: wrap;">
              <button type="button" class="df-btn df-btn-sm df-btn-danger" id="df-btn-retry">
                ${icons.refresh(14)} Retry Generation
              </button>
              <a href="/playground" class="df-btn df-btn-sm" data-link>
                ${icons.edit(14)} Edit Source Input
              </a>
            </div>
          </div>
        </div>
      </div>
    </main>
  `;

  const stagesList = document.getElementById('df-stages-list');
  const jobBadge = document.getElementById('df-job-badge');
  const jobTitle = document.getElementById('df-job-title');
  const jobSub = document.getElementById('df-job-sub');
  const scopeStats = document.getElementById('df-scope-stats');
  const elapsedTicker = document.getElementById('df-elapsed-ticker');
  const cancelWrapper = document.getElementById('df-cancel-wrapper');
  const cancelBtn = document.getElementById('df-btn-cancel');
  const errPanel = document.getElementById('df-error-panel');
  const errHeadline = document.getElementById('df-error-headline');
  const errText = document.getElementById('df-error-text');

  let timerInterval = null;
  let activeJobData = null;

  function updateElapsedDisplay() {
    const end = jobEndedAt || Date.now();
    const sec = Math.max(0, (end - jobStartedAt) / 1000).toFixed(1);
    if (elapsedTicker) {
      elapsedTicker.innerHTML = `${icons.clock(12)} ${sec} s`;
    }
  }

  function updateScopeStatsDisplay(proj) {
    if (!proj || !scopeStats) return;
    const bytes = new Blob([proj.code || '']).size;
    let fileCount = 1;
    if (proj.code && proj.code.includes('<<<DOCUFORGE:FILE_NAME="')) {
      const matches = proj.code.match(/<<<DOCUFORGE:FILE_NAME="([^"]+)">>>/g);
      if (matches) fileCount = matches.length;
    } else if (proj.code && proj.code.includes('# FILE: ')) {
      const matches = proj.code.match(/# FILE: /g);
      if (matches) fileCount = matches.length;
    }
    scopeStats.style.display = 'inline-flex';
    scopeStats.textContent = `${fileCount} file${fileCount === 1 ? '' : 's'} · ${formatBytes(bytes)}`;
  }

  function renderStages(job) {
    activeJobData = job;
    if (!stagesList || !job.stages) return;

    stagesList.innerHTML = job.stages.map((st, idx) => {
      const isRunning = st.status === 'running';
      const isCompleted = st.status === 'completed';
      const isFailed = st.status === 'failed';

      let durationText = '';
      if (isCompleted && st.duration_ms !== null) {
        durationText = st.duration_ms < 1000 ? `${st.duration_ms} ms` : `${(st.duration_ms / 1000).toFixed(1)} s`;
      } else if (isRunning && st.started_at) {
        const elapsed = Math.max(0, ((Date.now() / 1000) - st.started_at)).toFixed(1);
        durationText = `${elapsed} s in flight`;
      }

      const statusColor = isCompleted ? 'var(--status-ok)' :
                          isFailed ? 'var(--status-err)' :
                          isRunning ? 'var(--accent)' : 'var(--text-tertiary)';

      const statusIcon = isCompleted ? icons.check(18) :
                         isFailed ? icons.alert(18) :
                         isRunning ? icons.spinner(18) :
                         icons.mark(18);

      return `
        <div style="display: flex; align-items: flex-start; gap: 14px; padding: 14px 16px; border-radius: var(--r-md); background: ${isRunning ? 'var(--bg-surface-active)' : 'var(--bg-surface-elevated)'}; border: 1px solid ${isRunning ? 'var(--accent-border)' : 'var(--border-subtle)'}; transition: all var(--trans-fast);">
          <div style="margin-top: 2px; color: ${statusColor}; flex-shrink: 0;">
            ${statusIcon}
          </div>
          <div style="flex: 1; min-width: 0;">
            <div style="display: flex; align-items: center; justify-content: space-between; gap: 8px;">
              <b style="font-size: var(--fs-sm); color: ${isRunning ? 'var(--text-primary)' : (isCompleted ? 'var(--text-primary)' : 'var(--text-secondary)')};">
                ${idx + 1}. ${escapeHtml(st.label)}
              </b>
              ${durationText ? `<span class="df-mono df-sub" style="font-size: var(--fs-xs); color: ${isRunning ? 'var(--accent)' : 'var(--text-tertiary)'};">${durationText}</span>` : ''}
            </div>
            <div class="df-sub" style="font-size: var(--fs-xs); margin-top: 3px;">
              ${escapeHtml(st.description)}
            </div>
          </div>
        </div>
      `;
    }).join('');
  }

  // Cancel Handler
  if (cancelBtn) {
    cancelBtn.onclick = async () => {
      try {
        cancelBtn.disabled = true;
        cancelBtn.innerHTML = `${icons.spinner(14)} Cancelling...`;
        await api.cancelJob(jobId);
        showToast('Analysis cancellation requested');
      } catch (err) {
        showToast(err.message, true);
        cancelBtn.disabled = false;
        cancelBtn.innerHTML = `${icons.close(14)} Cancel Analysis`;
      }
    };
  }

  // Periodic ticker for live in-flight timer and total elapsed time
  timerInterval = setInterval(() => {
    updateElapsedDisplay();
    if (activeJobData && activeJobData.status === 'running') {
      renderStages(activeJobData);
    }
  }, 100);

  // Connect to SSE stream
  const unsubscribe = api.streamJob(jobId, (job) => {
    setActiveJob(job);
    renderStages(job);

    if (job.status === 'completed') {
      jobEndedAt = Date.now();
      clearInterval(timerInterval);
      updateElapsedDisplay();
      if (cancelWrapper) cancelWrapper.style.display = 'none';

      if (jobBadge) {
        jobBadge.className = 'df-badge df-badge-documented';
        jobBadge.innerHTML = `${icons.check(12)} Complete`;
      }
      if (jobTitle) {
        jobTitle.textContent = 'Documentation Ready!';
      }
      if (jobSub) {
        jobSub.textContent = 'Synthesized technical documentation successfully.';
      }
      showToast('Documentation successfully generated!');
      setTimeout(() => {
        navigate(`/documentation?project_id=${job.project_id}`);
      }, 700);
    } else if (job.status === 'failed') {
      jobEndedAt = Date.now();
      clearInterval(timerInterval);
      updateElapsedDisplay();
      if (cancelWrapper) cancelWrapper.style.display = 'none';

      if (jobBadge) {
        jobBadge.className = 'df-badge df-badge-failed';
        jobBadge.innerHTML = `${icons.alert(12)} Failed`;
      }
      if (jobTitle) {
        jobTitle.textContent = 'Analysis Failed';
      }
      if (errPanel && errText) {
        errHeadline.textContent = 'Generation encountered an error';
        errText.textContent = job.error || 'Gemini processing failed. Please verify API key or try again.';
        errPanel.style.display = 'block';

        const retryBtn = document.getElementById('df-btn-retry');
        if (retryBtn) {
          retryBtn.onclick = async () => {
            try {
              retryBtn.disabled = true;
              retryBtn.innerHTML = `${icons.spinner(14)} Retrying...`;
              const newJob = await api.createJob(job.project_id);
              setActiveJob(newJob);
              navigate(`/processing?job_id=${newJob.id}`, true);
            } catch (e) {
              showToast(e.message, true);
              retryBtn.disabled = false;
              retryBtn.innerHTML = `${icons.refresh(14)} Retry Generation`;
            }
          };
        }
      }
    } else if (job.status === 'cancelled') {
      jobEndedAt = Date.now();
      clearInterval(timerInterval);
      updateElapsedDisplay();
      if (cancelWrapper) cancelWrapper.style.display = 'none';

      if (jobBadge) {
        jobBadge.className = 'df-badge df-badge-draft';
        jobBadge.innerHTML = `${icons.close(12)} Cancelled`;
      }
      if (jobTitle) {
        jobTitle.textContent = 'Analysis Cancelled';
      }
      if (errPanel && errText) {
        errHeadline.textContent = 'Analysis was cancelled';
        errText.textContent = 'The documentation generation run was stopped before completion.';
        errPanel.style.display = 'block';

        const retryBtn = document.getElementById('df-btn-retry');
        if (retryBtn) {
          retryBtn.onclick = async () => {
            try {
              retryBtn.disabled = true;
              retryBtn.innerHTML = `${icons.spinner(14)} Retrying...`;
              const newJob = await api.createJob(job.project_id);
              setActiveJob(newJob);
              navigate(`/processing?job_id=${newJob.id}`, true);
            } catch (e) {
              showToast(e.message, true);
              retryBtn.disabled = false;
              retryBtn.innerHTML = `${icons.refresh(14)} Retry Generation`;
            }
          };
        }
      }
    }
  }, (err) => {
    console.warn('SSE stream disconnected, polling job state...', err);
    const pollInterval = setInterval(async () => {
      try {
        const j = await api.getJob(jobId);
        setActiveJob(j);
        renderStages(j);
        if (j.status === 'completed' || j.status === 'failed' || j.status === 'cancelled') {
          clearInterval(pollInterval);
        }
      } catch (e) {
        clearInterval(pollInterval);
      }
    }, 1000);
  });

  // Fetch initial job state and project details immediately
  try {
    const initialJob = await api.getJob(jobId);
    if (initialJob.created_at) {
      jobStartedAt = new Date(initialJob.created_at).getTime() || Date.now();
    }
    renderStages(initialJob);

    if (initialJob.project_id) {
      if (!project || String(project.id) !== String(initialJob.project_id)) {
        project = await api.getProject(initialJob.project_id);
      }
      updateScopeStatsDisplay(project);
    }
  } catch (e) {
    console.error('Failed to load initial job state', e);
  }
}

function formatBytes(bytes) {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

function escapeHtml(str) {
  return String(str ?? '').replace(/[&<>"']/g, c => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[c]));
}
