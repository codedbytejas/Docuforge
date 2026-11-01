/**
 * DocuForge AI — Application State & Preferences
 */

export const LANGS = [
  'Python', 'JavaScript', 'TypeScript', 'Java', 'C', 'C++', 'Go', 'PHP', 'Ruby', 'Rust', 'Other'
];

export const DOC_TYPES = [
  'Complete technical documentation',
  'Complete README',
  'Function documentation',
  'Class documentation',
  'API documentation'
];

export const SECTIONS_META = {
  readme: 'README',
  functions: 'Functions',
  classes: 'Classes',
  usage: 'Usage Examples',
  api: 'API Reference',
  dependencies: 'Dependencies',
  architecture: 'Architecture'
};

export const state = {
  status: { gemini_configured: false, model: 'gemini-3.5-flash', sections: [] },
  projects: [],
  currentProject: null,
  activeJob: null,
  currentRoute: '/',
  introCompleted: sessionStorage.getItem('df_intro_done') === 'true',
  theme: localStorage.getItem('df_theme') || 'dark',
  defaultLang: localStorage.getItem('df_default_lang') || 'Python',
  defaultDocType: localStorage.getItem('df_default_doc_type') || 'Complete technical documentation',
  listeners: new Set()
};

export function subscribe(fn) {
  state.listeners.add(fn);
  return () => state.listeners.delete(fn);
}

export function notify() {
  for (const fn of state.listeners) {
    try { fn(state); } catch (e) { console.error('State listener error', e); }
  }
}

export function setTheme(theme) {
  state.theme = theme;
  localStorage.setItem('df_theme', theme);
  document.documentElement.dataset.theme = theme;
  notify();
}

export function toggleTheme() {
  setTheme(state.theme === 'dark' ? 'light' : 'dark');
}

export function setCurrentProject(p) {
  state.currentProject = p;
  if (p?.id) {
    sessionStorage.setItem('df_active_project_id', String(p.id));
  } else {
    sessionStorage.removeItem('df_active_project_id');
  }
  notify();
}

export function setActiveJob(job) {
  state.activeJob = job;
  if (job?.id) {
    sessionStorage.setItem('df_active_job_id', job.id);
  } else {
    sessionStorage.removeItem('df_active_job_id');
  }
  notify();
}

export function setIntroDone() {
  state.introCompleted = true;
  sessionStorage.setItem('df_intro_done', 'true');
  notify();
}

