/**
 * Scholar AI — script.js
 * Frontend logic: chat interface, particles, animations, API calls
 * ──────────────────────────────────────────────────────────────────
 */

/* ══════════════════════════════════════════════════════════════════
   CONFIGURATION
   ══════════════════════════════════════════════════════════════════ */
const CONFIG = {
  API_BASE:          'http://localhost:5000',
  HEALTH_INTERVAL:   10_000,   // ms — how often to ping /health
  TYPING_SPEED:      45,       // ms per character for typewriter
  PARTICLE_COUNT:    55,
  CHAT_HISTORY_KEY:  'scholar_ai_chat_history',
};

/* ══════════════════════════════════════════════════════════════════
   DOM REFERENCES
   ══════════════════════════════════════════════════════════════════ */
const DOM = {
  sidebar:          document.getElementById('sidebar'),
  sidebarToggle:    document.getElementById('sidebar-toggle'),
  mainContent:      document.getElementById('main-content'),
  mobileMenuBtn:    document.getElementById('mobile-menu-btn'),
  statusDot:        document.getElementById('status-dot'),
  statusText:       document.getElementById('status-text'),
  chatMessages:     document.getElementById('chat-messages'),
  chatForm:         document.getElementById('chat-form'),
  chatInput:        document.getElementById('chat-input'),
  sendBtn:          document.getElementById('send-btn'),
  clearChatBtn:     document.getElementById('clear-chat-btn'),
  agentStatus:      document.getElementById('agent-status'),
  typewriterTarget: document.getElementById('typewriter-target'),
  activityFeed:     document.getElementById('activity-feed'),
  navLinks:         document.querySelectorAll('.nav-link'),
  chips:            document.querySelectorAll('.chip'),
  canvas:           document.getElementById('particles-canvas'),
  statNumbers:      document.querySelectorAll('.dash-stat-num'),
};

/* ══════════════════════════════════════════════════════════════════
   APPLICATION STATE
   ══════════════════════════════════════════════════════════════════ */
const STATE = {
  isLoading:    false,
  chatHistory:  [],  // { role: 'user'|'ai', content: string }
  sidebarOpen:  window.innerWidth > 768,
};

/* ══════════════════════════════════════════════════════════════════
   INIT
   ══════════════════════════════════════════════════════════════════ */
document.addEventListener('DOMContentLoaded', () => {
  initParticles();
  initTypewriter();
  initSidebar();
  initNavHighlighting();
  initChat();
  initDashboard();
  initSuggestionChips();
  checkApiHealth();
  setInterval(checkApiHealth, CONFIG.HEALTH_INTERVAL);
});

/* ══════════════════════════════════════════════════════════════════
   1. PARTICLE SYSTEM
   ══════════════════════════════════════════════════════════════════ */
function initParticles() {
  const canvas = DOM.canvas;
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  let particles = [];
  let animId;

  function resize() {
    canvas.width  = window.innerWidth;
    canvas.height = window.innerHeight;
  }

  function createParticle() {
    return {
      x:     Math.random() * canvas.width,
      y:     Math.random() * canvas.height,
      r:     Math.random() * 1.5 + 0.5,
      dx:    (Math.random() - 0.5) * 0.35,
      dy:    (Math.random() - 0.5) * 0.35,
      alpha: Math.random() * 0.5 + 0.1,
      hue:   Math.random() > 0.5 ? 230 : 200,   // indigo vs sky
    };
  }

  function drawParticles() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    particles.forEach(p => {
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fillStyle = `hsla(${p.hue}, 80%, 70%, ${p.alpha})`;
      ctx.fill();

      // Move
      p.x += p.dx;
      p.y += p.dy;

      // Wrap around edges
      if (p.x < 0)             p.x = canvas.width;
      if (p.x > canvas.width)  p.x = 0;
      if (p.y < 0)             p.y = canvas.height;
      if (p.y > canvas.height) p.y = 0;
    });

    // Draw faint connection lines between nearby particles
    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const dx = particles[i].x - particles[j].x;
        const dy = particles[i].y - particles[j].y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < 120) {
          ctx.beginPath();
          ctx.moveTo(particles[i].x, particles[i].y);
          ctx.lineTo(particles[j].x, particles[j].y);
          ctx.strokeStyle = `rgba(129,140,248,${0.06 * (1 - dist / 120)})`;
          ctx.lineWidth = 0.5;
          ctx.stroke();
        }
      }
    }

    animId = requestAnimationFrame(drawParticles);
  }

  resize();
  particles = Array.from({ length: CONFIG.PARTICLE_COUNT }, createParticle);
  drawParticles();

  window.addEventListener('resize', () => {
    cancelAnimationFrame(animId);
    resize();
    drawParticles();
  });
}

/* ══════════════════════════════════════════════════════════════════
   2. TYPEWRITER ANIMATION
   ══════════════════════════════════════════════════════════════════ */
function initTypewriter() {
  const el = DOM.typewriterTarget;
  if (!el) return;

  const phrases = [
    'with AI.',
    'faster.',
    'smarter.',
    'deeper.',
    'with IBM watsonx.',
  ];

  let phraseIdx = 0;
  let charIdx   = 0;
  let deleting  = false;
  let paused    = false;

  function tick() {
    const phrase = phrases[phraseIdx];

    if (paused) {
      setTimeout(tick, 1600);
      paused = false;
      return;
    }

    if (!deleting) {
      el.textContent = phrase.slice(0, ++charIdx);
      if (charIdx === phrase.length) {
        paused    = true;
        deleting  = true;
        setTimeout(tick, 1600);
        return;
      }
    } else {
      el.textContent = phrase.slice(0, --charIdx);
      if (charIdx === 0) {
        deleting  = false;
        phraseIdx = (phraseIdx + 1) % phrases.length;
      }
    }

    const speed = deleting ? CONFIG.TYPING_SPEED / 2 : CONFIG.TYPING_SPEED;
    setTimeout(tick, speed);
  }

  tick();
}

/* ══════════════════════════════════════════════════════════════════
   3. SIDEBAR LOGIC
   ══════════════════════════════════════════════════════════════════ */
function initSidebar() {
  // Desktop toggle
  DOM.sidebarToggle?.addEventListener('click', () => {
    STATE.sidebarOpen = !STATE.sidebarOpen;
    DOM.sidebar.classList.toggle('collapsed', !STATE.sidebarOpen);
    DOM.mainContent.classList.toggle('sidebar-hidden', !STATE.sidebarOpen);
    DOM.sidebarToggle.setAttribute('aria-expanded', STATE.sidebarOpen);
  });

  // Mobile hamburger
  DOM.mobileMenuBtn?.addEventListener('click', () => {
    DOM.sidebar.classList.toggle('mobile-open');
  });

  // Close sidebar on mobile when a nav link is clicked
  DOM.navLinks.forEach(link => {
    link.addEventListener('click', () => {
      if (window.innerWidth <= 768) {
        DOM.sidebar.classList.remove('mobile-open');
      }
    });
  });

  // Close sidebar on outside click (mobile)
  document.addEventListener('click', e => {
    if (
      window.innerWidth <= 768 &&
      DOM.sidebar.classList.contains('mobile-open') &&
      !DOM.sidebar.contains(e.target) &&
      !DOM.mobileMenuBtn.contains(e.target)
    ) {
      DOM.sidebar.classList.remove('mobile-open');
    }
  });
}

/* ══════════════════════════════════════════════════════════════════
   4. NAV HIGHLIGHTING (Intersection Observer)
   ══════════════════════════════════════════════════════════════════ */
function initNavHighlighting() {
  const sections = document.querySelectorAll('section[id]');

  const observer = new IntersectionObserver(
    entries => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          DOM.navLinks.forEach(link => {
            const active = link.dataset.section === entry.target.id;
            link.classList.toggle('active', active);
            link.setAttribute('aria-current', active ? 'page' : 'false');
          });
        }
      });
    },
    { rootMargin: '-40% 0px -40% 0px', threshold: 0 }
  );

  sections.forEach(s => observer.observe(s));
}

/* ══════════════════════════════════════════════════════════════════
   5. API HEALTH CHECK
   ══════════════════════════════════════════════════════════════════ */
async function checkApiHealth() {
  setStatus('checking', 'Checking…');
  try {
    const res = await fetch(`${CONFIG.API_BASE}/health`, {
      signal: AbortSignal.timeout(5000),
    });
    if (res.ok) {
      const data = await res.json();
      setStatus('online', data.status === 'healthy' ? 'API Online' : 'API Degraded');
    } else {
      setStatus('offline', 'API Error');
    }
  } catch {
    setStatus('offline', 'API Offline');
  }
}

function setStatus(state, text) {
  if (!DOM.statusDot || !DOM.statusText) return;
  DOM.statusDot.className = `status-dot ${state}`;
  DOM.statusText.textContent = text;
}

/* ══════════════════════════════════════════════════════════════════
   6. CHAT INTERFACE
   ══════════════════════════════════════════════════════════════════ */
function initChat() {
  loadChatHistory();

  // Welcome message if history is empty
  if (STATE.chatHistory.length === 0) {
    appendMessage(
      'ai',
      "👋 Hello! I'm **Scholar AI**, your IBM watsonx-powered research assistant.\n\nI can help you:\n• **Summarise** academic papers\n• **Explain** complex research concepts\n• **Find** citations and references\n• **Analyse** research trends\n\nWhat would you like to explore today?"
    );
  }

  // Form submission
  DOM.chatForm?.addEventListener('submit', async e => {
    e.preventDefault();
    const query = DOM.chatInput.value.trim();
    if (!query || STATE.isLoading) return;
    await sendMessage(query);
  });

  // Shift+Enter = newline, Enter = submit
  DOM.chatInput?.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      DOM.chatForm.dispatchEvent(new Event('submit'));
    }
  });

  // Auto-resize textarea
  DOM.chatInput?.addEventListener('input', () => {
    DOM.chatInput.style.height = 'auto';
    DOM.chatInput.style.height = Math.min(DOM.chatInput.scrollHeight, 160) + 'px';
  });

  // Clear chat
  DOM.clearChatBtn?.addEventListener('click', clearChat);
}

async function sendMessage(text) {
  STATE.isLoading = true;
  DOM.sendBtn.disabled = true;
  DOM.chatInput.value  = '';
  DOM.chatInput.style.height = 'auto';

  // Add user message to UI + history
  appendMessage('user', text);
  STATE.chatHistory.push({ role: 'user', content: text });

  // Show typing indicator
  const typingEl = showTypingIndicator();

  // Update agent status
  setAgentStatus('Thinking…', true);

  // Add activity feed entry
  addActivity(`Query: "${text.length > 40 ? text.slice(0, 40) + '…' : text}"`);

  try {
    const res = await fetch(`${CONFIG.API_BASE}/chat`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({
        message: text,
        history: STATE.chatHistory.slice(-10), // last 10 turns for context
      }),
      signal: AbortSignal.timeout(30_000),
    });

    typingEl.remove();

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.error || `HTTP ${res.status}`);
    }

    const data = await res.json();
    const reply = data.reply || 'I received your message but could not generate a response.';

    appendMessage('ai', reply);
    STATE.chatHistory.push({ role: 'ai', content: reply });
    saveChatHistory();

  } catch (err) {
    typingEl.remove();
    const errMsg = err.name === 'TimeoutError'
      ? '⚠️ The request timed out. Please try again.'
      : `⚠️ Could not reach the backend: **${err.message}**\n\nMake sure the Flask server is running on \`localhost:5000\`.`;
    appendMessage('ai', errMsg);
  } finally {
    STATE.isLoading = false;
    DOM.sendBtn.disabled = false;
    setAgentStatus('Ready to assist', false);
  }
}

function appendMessage(role, text) {
  const msgEl = document.createElement('div');
  msgEl.className = `message ${role}`;
  msgEl.innerHTML = `
    <div class="msg-avatar">${role === 'ai' ? 'AI' : 'You'}</div>
    <div class="msg-bubble">${markdownToHtml(text)}</div>
  `;
  DOM.chatMessages.appendChild(msgEl);
  DOM.chatMessages.scrollTop = DOM.chatMessages.scrollHeight;
  return msgEl;
}

function showTypingIndicator() {
  const el = document.createElement('div');
  el.className = 'message ai';
  el.innerHTML = `
    <div class="msg-avatar">AI</div>
    <div class="typing-indicator">
      <div class="typing-dot"></div>
      <div class="typing-dot"></div>
      <div class="typing-dot"></div>
    </div>
  `;
  DOM.chatMessages.appendChild(el);
  DOM.chatMessages.scrollTop = DOM.chatMessages.scrollHeight;
  return el;
}

function setAgentStatus(text, busy) {
  if (!DOM.agentStatus) return;
  DOM.agentStatus.textContent = text;
  DOM.agentStatus.style.color = busy
    ? 'var(--clr-warning)'
    : 'var(--clr-success)';
}

function clearChat() {
  DOM.chatMessages.innerHTML = '';
  STATE.chatHistory = [];
  saveChatHistory();
  appendMessage(
    'ai',
    '🗑️ Chat cleared. Ready for a fresh research session — what would you like to explore?'
  );
}

/* ──────────────────────────────────────────────
   Chat history — localStorage persistence
   ────────────────────────────────────────────── */
function saveChatHistory() {
  try {
    localStorage.setItem(CONFIG.CHAT_HISTORY_KEY, JSON.stringify(STATE.chatHistory));
  } catch { /* storage full or unavailable */ }
}

function loadChatHistory() {
  try {
    const saved = localStorage.getItem(CONFIG.CHAT_HISTORY_KEY);
    if (!saved) return;
    STATE.chatHistory = JSON.parse(saved);
    // Replay messages into DOM
    STATE.chatHistory.forEach(({ role, content }) => appendMessage(role, content));
  } catch {
    STATE.chatHistory = [];
  }
}

/* ──────────────────────────────────────────────
   Lightweight markdown → HTML converter
   Supports: **bold**, *italic*, `code`, \n bullets
   ────────────────────────────────────────────── */
function markdownToHtml(text) {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    // Bold
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    // Italic
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    // Inline code
    .replace(/`([^`]+)`/g, '<code style="font-family:\'JetBrains Mono\',monospace;background:rgba(255,255,255,0.08);padding:1px 5px;border-radius:4px;font-size:0.87em;">$1</code>')
    // Bullet list items starting with •
    .replace(/^• (.+)$/gm, '<li>$1</li>')
    // New lines → <br>
    .replace(/\n/g, '<br/>');
}

/* ══════════════════════════════════════════════════════════════════
   7. SUGGESTION CHIPS
   ══════════════════════════════════════════════════════════════════ */
function initSuggestionChips() {
  DOM.chips.forEach(chip => {
    chip.addEventListener('click', () => {
      const text = chip.textContent.trim();
      if (DOM.chatInput) {
        DOM.chatInput.value = text;
        DOM.chatInput.focus();
        // Auto-resize
        DOM.chatInput.style.height = 'auto';
        DOM.chatInput.style.height = DOM.chatInput.scrollHeight + 'px';
      }
      scrollToSection('chat');
    });
  });
}

/* ══════════════════════════════════════════════════════════════════
   8. DASHBOARD — ANIMATED COUNTERS + ACTIVITY FEED
   ══════════════════════════════════════════════════════════════════ */
function initDashboard() {
  animateCounters();
  seedActivityFeed();
}

function animateCounters() {
  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (!entry.isIntersecting) return;
      const el     = entry.target;
      const target = parseInt(el.dataset.target, 10);
      const suffix = el.dataset.suffix || '';
      const duration = 1600;
      const start    = performance.now();

      function update(now) {
        const elapsed  = now - start;
        const progress = Math.min(elapsed / duration, 1);
        // Ease-out cubic
        const eased = 1 - Math.pow(1 - progress, 3);
        el.textContent = Math.round(eased * target) + suffix;
        if (progress < 1) requestAnimationFrame(update);
      }

      requestAnimationFrame(update);
      observer.unobserve(el);
    });
  }, { threshold: 0.5 });

  DOM.statNumbers.forEach(el => observer.observe(el));
}

const ACTIVITY_TEMPLATES = [
  'Summarised paper: "Attention Is All You Need"',
  'Generated APA citation for arXiv:2310.01054',
  'Explained concept: Transformer architecture',
  'Searched: quantum error correction methods',
  'Trend analysis completed: NLP 2024',
  'Citation check: 14 sources verified',
  'Summarised paper: "RLHF Survey 2024"',
  'Keyword extraction: bioinformatics dataset',
];

function seedActivityFeed() {
  const feed = DOM.activityFeed;
  if (!feed) return;

  const now = Date.now();
  const recent = ACTIVITY_TEMPLATES.slice(0, 5);

  recent.forEach((text, i) => {
    const mins = (i + 1) * 3;
    appendActivityItem(text, `${mins}m ago`, i * 120);
  });
}

function addActivity(text) {
  appendActivityItem(text, 'just now', 0);
  // Trim to last 8 items
  const feed = DOM.activityFeed;
  if (feed && feed.children.length > 8) {
    feed.lastChild?.remove();
  }
}

function appendActivityItem(text, time, delayMs) {
  const feed = DOM.activityFeed;
  if (!feed) return;

  const li = document.createElement('li');
  li.className = 'activity-item';
  li.style.animationDelay = `${delayMs}ms`;
  li.innerHTML = `
    <span class="activity-dot"></span>
    <span class="activity-text">${escapeHtml(text)}</span>
    <span class="activity-time">${escapeHtml(time)}</span>
  `;
  feed.insertBefore(li, feed.firstChild);
}

/* ══════════════════════════════════════════════════════════════════
   UTILITIES
   ══════════════════════════════════════════════════════════════════ */

/** Smooth-scroll to a section by id */
function scrollToSection(id) {
  const el = document.getElementById(id);
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

/** Escape HTML entities */
function escapeHtml(str) {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

// Expose scrollToSection globally (used in inline HTML onclick attributes)
window.scrollToSection = scrollToSection;
