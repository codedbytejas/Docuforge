/**
 * DocuForge AI — History-based Router & Navigation Guards
 */

import { state, setCurrentProject, setActiveJob, toggleTheme } from './state.js';
import { icons } from './icons.js';
import { api, showToast } from './api.js';

export const routes = {};

export function registerRoute(path, handler) {
  routes[path] = handler;
}

export function parseUrl() {
  const path = window.location.pathname || '/';
  const searchParams = new URLSearchParams(window.location.search);
  return { path, params: searchParams };
}

export async function navigate(pathWithQuery, replace = false) {
  const [path, query] = pathWithQuery.split('?');
  const url = pathWithQuery;

  if (replace) {
    window.history.replaceState({}, '', url);
  } else {
    window.history.pushState({}, '', url);
  }

  await renderCurrentRoute();
}

export function renderNavbar(currentPath) {
  const isDark = state.theme === 'dark';
  const isPlaygroundOrProcessing = currentPath === '/playground' || currentPath === '/processing';
  const showCta = !isPlaygroundOrProcessing;

  return `
    <header class="df-navbar">
      <div class="df-navbar-inner">
        <a href="/" class="df-brand" data-link>
          <span class="df-brand-mark">${icons.mark(16)}</span>
          <span>DocuForge</span>
          <span class="df-brand-tag">AI</span>
        </a>

        <nav class="df-nav-links">
          <a href="/" class="df-nav-link ${currentPath === '/' ? 'active' : ''}" data-link>Home</a>
          <a href="/#problem" class="df-nav-link">The Problem</a>
          <a href="/#features" class="df-nav-link">Features</a>
          <a href="/#how-it-works" class="df-nav-link">How It Works</a>
          <a href="/#languages" class="df-nav-link">Languages</a>
          <a href="/#preview" class="df-nav-link">Preview</a>
          <a href="/#about" class="df-nav-link">About</a>
          <a href="/playground" class="df-nav-link ${currentPath === '/playground' ? 'active' : ''}" data-link>Playground</a>
          <a href="/projects" class="df-nav-link ${currentPath === '/projects' ? 'active' : ''}" data-link>Projects</a>
          <a href="/settings" class="df-nav-link ${currentPath === '/settings' ? 'active' : ''}" data-link>Settings</a>
        </nav>

        <div class="df-nav-actions">
          <button class="df-btn df-btn-ghost df-btn-icon" id="df-theme-btn" title="Toggle color theme" aria-label="Toggle theme">
            ${isDark ? icons.sun(16) : icons.moon(16)}
          </button>
          ${showCta ? `
            <a href="/playground" class="df-btn df-btn-primary df-btn-sm df-navbar-cta-desktop" data-link>
              Start Documenting ${icons.arrowRight(12)}
            </a>
          ` : ''}
          <button class="df-mobile-menu-btn" id="df-mobile-menu-btn" aria-label="Toggle navigation menu">
            ${icons.menu(18)}
          </button>
        </div>
      </div>

      <!-- Slide-down mobile drawer -->
      <div class="df-mobile-drawer" id="df-mobile-drawer">
        <a href="/" class="df-mobile-drawer-link ${currentPath === '/' ? 'active' : ''}" data-link>Home</a>
        <a href="/#problem" class="df-mobile-drawer-link">The Problem</a>
        <a href="/#features" class="df-mobile-drawer-link">Features</a>
        <a href="/#how-it-works" class="df-mobile-drawer-link">How It Works</a>
        <a href="/#languages" class="df-mobile-drawer-link">Languages</a>
        <a href="/#preview" class="df-mobile-drawer-link">Preview</a>
        <a href="/#about" class="df-mobile-drawer-link">About</a>
        <a href="/playground" class="df-mobile-drawer-link ${currentPath === '/playground' ? 'active' : ''}" data-link>Playground</a>
        <a href="/projects" class="df-mobile-drawer-link ${currentPath === '/projects' ? 'active' : ''}" data-link>Projects</a>
        <a href="/settings" class="df-mobile-drawer-link ${currentPath === '/settings' ? 'active' : ''}" data-link>Settings</a>
        ${showCta ? `
          <a href="/playground" class="df-btn df-btn-primary" data-link style="margin-top: 6px; width: 100%; justify-content: center;">
            Start Documenting ${icons.arrowRight(13)}
          </a>
        ` : ''}
      </div>
    </header>
  `;
}

export async function renderCurrentRoute() {
  const { path, params } = parseUrl();
  state.currentRoute = path;

  // Resolve matching route or fallback to home
  let matchedHandler = routes[path];
  if (!matchedHandler) {
    matchedHandler = routes['/'];
  }

  // Route Guards
  if (path === '/processing') {
    const jid = params.get('job_id') || sessionStorage.getItem('df_active_job_id');
    if (!jid) {
      showToast('No active generation job found. Redirecting to playground.');
      navigate('/playground', true);
      return;
    }
  }

  if (path === '/documentation') {
    const pid = params.get('project_id') || sessionStorage.getItem('df_active_project_id');
    if (!pid && !state.currentProject) {
      showToast('Select a project to view its documentation.');
      navigate('/projects', true);
      return;
    }
  }

  // Update active state in navigation
  document.querySelectorAll('.df-nav-link').forEach(link => {
    link.classList.toggle('active', link.getAttribute('href') === path);
  });

  // Execute route renderer
  const appContainer = document.getElementById('app-view');
  if (appContainer && matchedHandler) {
    await matchedHandler(appContainer, params);
  }

  // Re-bind theme button in navbar
  const themeBtn = document.getElementById('df-theme-btn');
  if (themeBtn) {
    themeBtn.onclick = () => {
      toggleTheme();
      const updatedIcon = state.theme === 'dark' ? icons.sun(16) : icons.moon(16);
      themeBtn.innerHTML = updatedIcon;
    };
  }

  // Bind mobile menu drawer toggle
  const mobileMenuBtn = document.getElementById('df-mobile-menu-btn');
  const mobileDrawer = document.getElementById('df-mobile-drawer');
  if (mobileMenuBtn && mobileDrawer) {
    mobileMenuBtn.onclick = (e) => {
      e.stopPropagation();
      const isOpen = mobileDrawer.classList.toggle('open');
      mobileMenuBtn.innerHTML = isOpen ? icons.close(18) : icons.menu(18);
    };

    mobileDrawer.querySelectorAll('a').forEach(link => {
      link.addEventListener('click', () => {
        mobileDrawer.classList.remove('open');
        mobileMenuBtn.innerHTML = icons.menu(18);
      });
    });

    document.addEventListener('click', (e) => {
      if (!mobileDrawer.contains(e.target) && !mobileMenuBtn.contains(e.target)) {
        if (mobileDrawer.classList.contains('open')) {
          mobileDrawer.classList.remove('open');
          mobileMenuBtn.innerHTML = icons.menu(18);
        }
      }
    });
  }

  // Active section scroll indicator on landing page
  if (path === '/') {
    const sections = ['problem', 'features', 'how-it-works', 'languages', 'about'];
    const navLinks = document.querySelectorAll('.df-nav-link');
    window.onscroll = () => {
      let activeId = '';
      const pos = window.scrollY + 140;
      for (const id of sections) {
        const el = document.getElementById(id);
        if (el && el.offsetTop <= pos) {
          activeId = id;
        }
      }
      navLinks.forEach(link => {
        const href = link.getAttribute('href') || '';
        if (href.startsWith('/#') || href.startsWith('#')) {
          const target = href.replace(/^(\/)?#/, '');
          link.classList.toggle('active', target === activeId);
        } else if (href === '/' && !activeId) {
          link.classList.add('active');
        }
      });
    };
  } else {
    window.onscroll = null;
  }

  window.scrollTo(0, 0);
}

export function initRouter() {
  // Intercept click on internal links & hash anchors
  document.addEventListener('click', (e) => {
    const hashTarget = e.target.closest('a[href^="#"], a[href^="/#"]');
    if (hashTarget) {
      const rawHref = hashTarget.getAttribute('href');
      const hash = rawHref.replace(/^(\/)?#/, '');
      const el = document.getElementById(hash);
      if (el) {
        e.preventDefault();
        el.scrollIntoView({ behavior: 'smooth' });
        return;
      }
    }

    const target = e.target.closest('a[data-link]');
    if (target) {
      const href = target.getAttribute('href');
      if (href && !href.startsWith('http') && !href.startsWith('mailto:') && !target.hasAttribute('download')) {
        e.preventDefault();
        navigate(href);
      }
    }
  });

  // Listen to browser forward/back
  window.addEventListener('popstate', () => {
    renderCurrentRoute();
  });
}

