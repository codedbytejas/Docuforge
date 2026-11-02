/**
 * DocuForge AI — API Client
 */

export async function request(path, options = {}) {
  const isForm = options.body instanceof FormData;
  const headers = isForm ? {} : { 'Content-Type': 'application/json', ...(options.headers || {}) };
  
  const res = await fetch('/api' + path, { ...options, headers });
  const data = await res.json().catch(() => ({}));
  
  if (!res.ok) {
    const message = typeof data.message === 'string' ? data.message : (typeof data.detail === 'string' ? data.detail : `Request failed (${res.status})`);
    const error = new Error(message);
    error.status = res.status;
    error.detail = data.detail;
    error.data = data;
    error.retryAfter = parseInt(res.headers.get('Retry-After') || data.retry_after_seconds || '0', 10);
    throw error;
  }
  return data;
}

export const api = {
  getStatus: () => request('/status'),
  getUsage: () => request('/usage'),
  getProjects: () => request('/projects'),
  getProject: (pid) => request(`/projects/${pid}`),
  createProject: (project) => request('/projects', { method: 'POST', body: JSON.stringify(project) }),
  updateProject: (pid, project) => request(`/projects/${pid}`, { method: 'PUT', body: JSON.stringify(project) }),
  deleteProject: (pid) => request(`/projects/${pid}`, { method: 'DELETE' }),
  
  uploadFiles: (files) => {
    const fd = new FormData();
    for (const f of files) {
      fd.append('files', f);
    }
    return request('/upload', { method: 'POST', body: fd });
  },

  createJob: (pid) => request(`/projects/${pid}/jobs`, { method: 'POST' }),
  getJob: (jid) => request(`/jobs/${jid}`),
  cancelJob: (jid) => request(`/jobs/${jid}/cancel`, { method: 'POST' }),

  streamJob: (jid, onEvent, onError) => {
    let source;
    try {
      source = new EventSource(`/api/jobs/${jid}/stream`);
    } catch (e) {
      if (onError) onError(e);
      return () => {};
    }

    source.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        if (onEvent) onEvent(data);
        if (data.status === 'completed' || data.status === 'failed' || data.status === 'cancelled') {
          source.close();
        }
      } catch (err) {
        console.error('SSE JSON error', err);
      }
    };

    source.onerror = (e) => {
      // EventSource reconnects automatically unless closed
      if (onError) onError(e);
    };

    return () => {
      source.close();
    };
  },

  generateDirect: (pid) => request(`/projects/${pid}/generate`, { method: 'POST' }),
  regenerateSection: (pid, section) => request(`/projects/${pid}/regenerate/${section}`, { method: 'POST' })
};

export function showToast(message, isError = false) {
  let container = document.getElementById('df-toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'df-toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = 'df-toast' + (isError ? ' err' : '');
  toast.textContent = message;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(8px)';
    toast.style.transition = 'all 180ms ease-out';
    setTimeout(() => toast.remove(), 200);
  }, 4000);
}

