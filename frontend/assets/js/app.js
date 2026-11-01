/**
 * DocuForge AI — Main Application Entry Point
 */

import { state } from './state.js';
import { api } from './api.js';
import { initRouter, registerRoute, navigate } from './router.js';
import { shouldShowIntro, playIntro } from './components/intro.js';
import { renderLandingPage } from './components/landing.js';
import { renderPlayground } from './components/playground.js';
import { renderProcessing } from './components/processing.js';
import { renderDocumentation } from './components/documentation.js';
import { renderProjects } from './components/projects.js';
import { renderSettings } from './components/settings.js';

// ==========================================
// View: Home / Landing with Cinematic Intro
// ==========================================
async function renderHome(container) {
  if (shouldShowIntro()) {
    playIntro(() => {
      renderLandingPage(container);
    });
  } else {
    renderLandingPage(container);
  }
}

// ==========================================
// Bootstrap
// ==========================================
async function init() {
  document.documentElement.dataset.theme = state.theme;

  // Register all 6 routes
  registerRoute('/', renderHome);
  registerRoute('/playground', renderPlayground);
  registerRoute('/processing', renderProcessing);
  registerRoute('/documentation', renderDocumentation);
  registerRoute('/projects', renderProjects);
  registerRoute('/settings', renderSettings);

  // Initialize router (link interception & popstate)
  initRouter();

  // Load status and projects from backend in parallel
  try {
    const [st, projs] = await Promise.all([api.getStatus(), api.getProjects()]);
    state.status = st;
    state.projects = projs;
  } catch (e) {
    console.error('Failed to load initial status or projects', e);
  }

  // Initial render based on browser location
  const fullPath = (window.location.pathname || '/') + (window.location.search || '');
  navigate(fullPath, true);
}

window.addEventListener('DOMContentLoaded', init);
