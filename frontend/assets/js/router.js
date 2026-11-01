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
    <a href="#main-content" class="df-skip-link">Skip to content</a>
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

const ROUTE_META = {
  '/': {
    title: 'DocuForge AI — Documentation without the busywork',
    desc: 'Turn your source code into clear, structured, developer-friendly documentation in seconds with Google Gemini.'
  },
  '/playground': {
    title: 'Playground — DocuForge AI',
    desc: 'Upload repository files or paste code to synthesize technical documentation with Google Gemini.'
  },
  '/processing': {
    title: 'Generating Documentation — DocuForge AI',
    desc: 'Real-time AI pipeline execution and code analysis runner.'
  },
  '/documentation': {
    title: 'Documentation Workspace — DocuForge AI',
    desc: 'Interactive documentation results workspace with in-place editing, markdown copy, and PDF export.'
  },
  '/projects': {
    title: 'Saved Projects — DocuForge AI',
    desc: 'Manage, search, rename, and export your documented codebase projects.'
  },
  '/settings': {
    title: 'Settings — DocuForge AI',
    desc: 'Configure system defaults, Gemini API status, and interface preferences.'
  },
  '404': {
    title: 'Page Not Found — DocuForge AI',
    desc: 'The requested page could not be found.'
  }
};

export function renderNotFound(container) {
  container.innerHTML = `
    ${renderNavbar('/404')}
    <main class="df-page" id="main-content" style="min-height: 70vh; display: flex; align-items: center; justify-content: center;">
      <div class="df-card" style="max-width: 520px; text-align: center; padding: 48px 28px; width: 100%;">
        <div class="df-badge" style="margin-bottom: 16px; color: var(--accent); border-color: var(--accent-border); background-color: var(--accent-dim);">
          404 Error &middot; Route Not Found
        </div>
        <h1 class="df-title-xl" style="margin-bottom: 12px;">This page does not exist.</h1>
        <p class="df-lead" style="margin: 0 auto 28px; font-size: 14.5px;">
          The route you navigated to was not recognized or may have moved.
        </p>
        <div style="display: flex; gap: 12px; justify-content: center; flex-wrap: wrap;">
          <a href="/" class="df-btn" data-link>
            ${icons.arrowLeft(14)} Return to Home
          </a>
          <a href="/playground" class="df-btn df-btn-primary" data-link>
            Start Documenting ${icons.arrowRight(14)}
          </a>
        </div>
      </div>
    </main>
  `;
}

export async function renderCurrentRoute() {
  const { path, params } = parseUrl();
  state.currentRoute = path;

  // Resolve matching route or fallback to 404
  let matchedHandler = routes[path];
  const is404 = !matchedHandler;

  // Update dynamic document title and meta description
  const meta = ROUTE_META[path] || (is404 ? ROUTE_META['404'] : ROUTE_META['/']);
  document.title = meta.title;
  const metaDescEl = document.getElementById('df-meta-desc');
  if (metaDescEl) {
    metaDescEl.setAttribute('content', meta.desc);
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

  // Execute route renderer or 404
  const appContainer = document.getElementById('app-view');
  if (appContainer) {
    if (matchedHandler) {
      await matchedHandler(appContainer, params);
    } else {
      renderNotFound(appContainer);
    }
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

