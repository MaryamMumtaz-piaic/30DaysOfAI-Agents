/**
 * AI Content Marketing Machine — Day 18
 * Frontend Application Logic
 * By Maryam Mumtaz — Marsa Empower
 */

// ============================================================
// DOM REFERENCES
// ============================================================
const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

const DOM = {
  // Form inputs
  brandName:       $('#brandName'),
  brandVoice:      $('#brandVoice'),
  targetAudience:  $('#targetAudience'),
  industry:        $('#industry'),
  weeklyTopic:     $('#weeklyTopic'),
  pillarInput:     $('#pillarInput'),
  pillarsContainer:$('#pillarsContainer'),
  presetButtons:   $('#presetButtons'),

  // Buttons
  generateBtn:     $('#generateBtn'),
  downloadPdfBtn:  $('#downloadPdfBtn'),
  newGenerationBtn:$('#newGenerationBtn'),

  // Panels
  welcomeState:    $('#welcomeState'),
  progressPanel:   $('#progressPanel'),
  progressBar:     $('#progressBar'),
  progressStatus:  $('#progressStatus'),
  progressAgents:  $('#progressAgents'),
  resultsContainer:$('#resultsContainer'),
  resultsArea:     $('#resultsArea'),

  // Tabs
  resultsTabs:     $('#resultsTabs'),

  // Tab Panels
  tabSeo:          $('#tab-seo'),
  tabBlog:         $('#tab-blog'),
  tabSocial:       $('#tab-social'),
  tabEmail:        $('#tab-email'),
  tabAds:          $('#tab-ads'),
  tabAnalytics:    $('#tab-analytics'),

  // Toast
  toastContainer:  $('#toastContainer'),
};

// ============================================================
// STATE
// ============================================================
let contentPillars = [];
let currentJobId = null;
let currentPreset = null;
let isGenerating = false;
let wsConnection = null;

// Agent mapping for progress tracking
const AGENTS = [
  { key: 'seo',       name: 'SEO Keyword Researcher' },
  { key: 'blog',      name: 'Long-Form Blog Writer' },
  { key: 'social',    name: 'Social Media Adaptor' },
  { key: 'email',     name: 'Email Newsletter Writer' },
  { key: 'ads',       name: 'Meta Ad Copy Generator' },
  { key: 'analytics', name: 'Analytics Predictor' },
];

// ============================================================
// INITIALIZATION
// ============================================================
document.addEventListener('DOMContentLoaded', () => {
  initPresetButtons();
  initPillarInput();
  initGenerateButton();
  initTabNavigation();
  initDownloadButton();
  initNewGenerationButton();
});

// ============================================================
// PRESET BUTTONS
// ============================================================
function initPresetButtons() {
  $$('.preset-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const presetKey = btn.dataset.preset;
      loadPreset(presetKey);
    });
  });
}

async function loadPreset(presetKey) {
  try {
    const resp = await fetch('/presets');
    if (!resp.ok) throw new Error('Failed to fetch presets');
    const presets = await resp.json();
    const preset = presets[presetKey];
    if (!preset) {
      showToast('error', 'Preset Not Found', `Preset "${presetKey}" is not available.`);
      return;
    }

    // Fill form
    DOM.brandName.value      = preset.brand_name || '';
    DOM.brandVoice.value     = preset.brand_voice || '';
    DOM.targetAudience.value = preset.target_audience || '';
    DOM.industry.value       = preset.industry || '';
    DOM.weeklyTopic.value    = preset.weekly_topic || '';

    // Set pillars
    contentPillars = [...(preset.content_pillars || [])];
    renderPillars();

    // Highlight active preset button
    $$('.preset-btn').forEach(b => b.classList.remove('active'));
    const activeBtn = $(`[data-preset="${presetKey}"]`);
    if (activeBtn) activeBtn.classList.add('active');
    currentPreset = presetKey;

    showToast('success', 'Preset Loaded', `${preset.brand_name} configuration applied.`);
  } catch (err) {
    console.error('Preset load error:', err);
    showToast('error', 'Load Error', 'Could not load presets from server.');
  }
}

// ============================================================
// CONTENT PILLARS (Tag Input)
// ============================================================
function initPillarInput() {
  DOM.pillarInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      const value = DOM.pillarInput.value.trim();
      if (value && !contentPillars.includes(value)) {
        contentPillars.push(value);
        renderPillars();
        DOM.pillarInput.value = '';
      }
    }
  });
}

function renderPillars() {
  DOM.pillarsContainer.innerHTML = contentPillars.map((pillar, i) => `
    <span class="tag" data-index="${i}">
      ${escapeHtml(pillar)}
      <button class="tag-remove" type="button" aria-label="Remove ${escapeHtml(pillar)}" onclick="removePillar(${i})">&times;</button>
    </span>
  `).join('');
}

function removePillar(index) {
  contentPillars.splice(index, 1);
  renderPillars();
}

// Make removePillar globally accessible
window.removePillar = removePillar;

// ============================================================
// GENERATE BUTTON & WEBSOCKET
// ============================================================
function initGenerateButton() {
  DOM.generateBtn.addEventListener('click', () => {
    if (isGenerating) return;
    startGeneration();
  });
}

function startGeneration() {
  // Validate
  const brandName = DOM.brandName.value.trim();
  const weeklyTopic = DOM.weeklyTopic.value.trim();

  if (!brandName) {
    showToast('error', 'Validation Error', 'Brand name is required.');
    DOM.brandName.focus();
    return;
  }

  if (!weeklyTopic) {
    showToast('error', 'Validation Error', 'Weekly topic is required.');
    DOM.weeklyTopic.focus();
    return;
  }

  isGenerating = true;
  currentJobId = null;

  // Prepare payload
  const payload = {
    brand_name:      brandName,
    brand_voice:     DOM.brandVoice.value.trim() || 'Professional and authoritative.',
    target_audience: DOM.targetAudience.value.trim() || 'General audience.',
    industry:        DOM.industry.value.trim() || 'Technology',
    weekly_topic:    weeklyTopic,
    brand_colors:    '',
    content_pillars: contentPillars.length > 0 ? contentPillars : ['General'],
  };

  // UI state
  DOM.welcomeState.classList.add('hidden');
  DOM.resultsContainer.classList.add('hidden');
  DOM.progressPanel.classList.remove('hidden');
  DOM.generateBtn.disabled = true;
  DOM.generateBtn.innerHTML = `<span class="btn-spinner"></span> Generating...`;

  resetProgressSteps();
  connectWebSocket(payload);
}

function connectWebSocket(payload) {
  const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${protocol}//${location.host}/ws/generate`;

  try {
    wsConnection = new WebSocket(wsUrl);

    wsConnection.onopen = () => {
      wsConnection.send(JSON.stringify(payload));
      updateProgressStatus('Connected — Running pipeline...');
    };

    wsConnection.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        handleWSMessage(msg);
      } catch (err) {
        console.error('WS parse error:', err);
      }
    };

    wsConnection.onerror = (err) => {
      console.error('WebSocket error:', err);
      showToast('error', 'Connection Error', 'Failed to connect to the server.');
      resetUI();
    };

    wsConnection.onclose = () => {
      wsConnection = null;
      if (isGenerating && !currentJobId) {
        // Unexpected close
        showToast('error', 'Connection Lost', 'WebSocket closed unexpectedly.');
        resetUI();
      }
    };
  } catch (err) {
    console.error('WS connection failed:', err);
    showToast('error', 'Connection Failed', 'Could not establish WebSocket connection.');
    resetUI();
  }
}

function handleWSMessage(msg) {
  switch (msg.type) {
    case 'progress':
      handleProgress(msg);
      break;
    case 'result':
      handleResult(msg);
      break;
    case 'error':
      showToast('error', 'Pipeline Error', msg.message || 'An error occurred during generation.');
      resetUI();
      break;
    default:
      console.warn('Unknown message type:', msg.type);
  }
}

function handleProgress(msg) {
  const stage = msg.stage || '';
  const message = msg.message || '';

  // Map stage to agent key
  const agentKey = stage.toLowerCase().replace(/[^a-z]/g, '');
  const agentIndex = AGENTS.findIndex(a => agentKey.includes(a.key));

  if (agentIndex >= 0) {
    updateAgentStep(agentIndex, 'active', message);

    // Mark previous agents as completed
    for (let i = 0; i < agentIndex; i++) {
      const stepEl = DOM.progressAgents.children[i];
      if (!stepEl.classList.contains('completed')) {
        updateAgentStep(i, 'completed', 'Done');
      }
    }

    // Update progress bar
    const progress = Math.min(((agentIndex + 1) / AGENTS.length) * 100, 95);
    DOM.progressBar.style.width = `${progress}%`;
  }

  updateProgressStatus(message);
}

function handleResult(msg) {
  isGenerating = false;
  currentJobId = msg.job_id;
  const data = msg.data;

  // Complete all progress steps
  for (let i = 0; i < AGENTS.length; i++) {
    updateAgentStep(i, 'completed', 'Completed');
  }
  DOM.progressBar.style.width = '100%';
  updateProgressStatus('All agents completed!');

  // Short delay for visual satisfaction
  setTimeout(() => {
    renderResults(data);
    DOM.progressPanel.classList.add('hidden');
    DOM.resultsContainer.classList.remove('hidden');
    DOM.generateBtn.disabled = false;
    DOM.generateBtn.innerHTML = `<svg viewBox="0 0 24 24"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg> Generate Content Marketing Suite`;
    showToast('success', 'Content Suite Ready', 'Your complete content marketing suite has been generated.');
  }, 800);
}

// ============================================================
// PROGRESS UI HELPERS
// ============================================================
function resetProgressSteps() {
  const steps = DOM.progressAgents.children;
  for (let i = 0; i < steps.length; i++) {
    steps[i].className = 'agent-step pending';
    steps[i].querySelector('.agent-step-detail').textContent = 'Waiting...';
    steps[i].querySelector('.agent-step-time').textContent = '—';
  }
  DOM.progressBar.style.width = '0%';
  updateProgressStatus('Initializing...');
}

function updateAgentStep(index, state, detail) {
  const step = DOM.progressAgents.children[index];
  if (!step) return;

  step.className = `agent-step ${state}`;
  step.querySelector('.agent-step-detail').textContent = detail;

  if (state === 'completed') {
    step.querySelector('.agent-step-time').textContent = '✓';
    step.querySelector('.agent-step-icon').innerHTML = `<svg viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg>`;
  } else if (state === 'active') {
    step.querySelector('.agent-step-time').textContent = '...';
  }
}

function updateProgressStatus(text) {
  const statusText = DOM.progressStatus.querySelector('span:last-child') || DOM.progressStatus;
  // Keep the spinner, update text
  const spinner = DOM.progressStatus.querySelector('.btn-spinner');
  if (spinner) {
    DOM.progressStatus.innerHTML = '';
    DOM.progressStatus.appendChild(spinner);
    const textEl = document.createElement('span');
    textEl.textContent = text;
    DOM.progressStatus.appendChild(textEl);
  } else {
    DOM.progressStatus.textContent = text;
  }
}

function resetUI() {
  isGenerating = false;
  DOM.generateBtn.disabled = false;
  DOM.generateBtn.innerHTML = `<svg viewBox="0 0 24 24"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg> Generate Content Marketing Suite`;
  DOM.progressPanel.classList.add('hidden');
  DOM.welcomeState.classList.remove('hidden');

  if (wsConnection) {
    try { wsConnection.close(); } catch(e) {}
    wsConnection = null;
  }
}

// ============================================================
// RENDER RESULTS
// ============================================================
function renderResults(data) {
  renderSEOTab(data.seo_keywords || {});
  renderBlogTab(data.blog_post || {});
  renderSocialTab(data.social_media || {});
  renderEmailTab(data.email_newsletter || {});
  renderAdsTab(data.ad_copy || {});
  renderAnalyticsTab(data.analytics || {});
}

// ---------- SEO Keywords Tab ----------
function renderSEOTab(seo) {
  const keywords = seo.keywords || [];
  const summary = seo.summary || '';

  DOM.tabSeo.innerHTML = `
    <div class="result-card">
      <div class="result-card-header">
        <h3>
          <svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
          SEO Keyword Research
        </h3>
        <button class="copy-btn" onclick="copyToClipboard('seo-table')" aria-label="Copy keyword data">
          <svg viewBox="0 0 24 24"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>
          Copy
        </button>
      </div>
      <div class="result-card-body">
        ${summary ? `<p style="margin-bottom:var(--space-4);color:var(--slate-600);font-size:var(--font-size-sm);line-height:1.7">${escapeHtml(summary)}</p>` : ''}
        <div id="seo-table">
          <table class="keyword-table">
            <thead>
              <tr>
                <th>Keyword</th>
                <th>Volume</th>
                <th>Competition</th>
                <th>Intent</th>
                <th>Difficulty</th>
              </tr>
            </thead>
            <tbody>
              ${keywords.map(kw => `
                <tr>
                  <td><strong>${escapeHtml(kw.keyword || '')}</strong></td>
                  <td>${formatNumber(kw.search_volume || 0)}</td>
                  <td>${escapeHtml(kw.competition || 'Medium')}</td>
                  <td><span class="intent-badge intent-${(kw.intent || 'informational').toLowerCase()}">${escapeHtml(kw.intent || 'Informational')}</span></td>
                  <td><span class="difficulty-badge difficulty-${getDifficultyClass(kw.difficulty || 50)}">${kw.difficulty || 50}/100</span></td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  `;
}

// ---------- Blog Post Tab ----------
function renderBlogTab(blog) {
  const sections = blog.sections || [];

  DOM.tabBlog.innerHTML = `
    <div class="result-card">
      <div class="result-card-header">
        <h3>
          <svg viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
          SEO Blog Post
        </h3>
        <button class="copy-btn" onclick="copyToClipboard('blog-content')" aria-label="Copy blog post">
          <svg viewBox="0 0 24 24"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>
          Copy
        </button>
      </div>
      <div class="result-card-body">
        <div class="blog-preview" id="blog-content">
          <div class="blog-meta">
            <div class="blog-meta-item">
              <svg viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
              Word Count: <strong>${formatNumber(blog.word_count || 0)}</strong>
            </div>
            <div class="blog-meta-item">
              <svg viewBox="0 0 24 24"><path d="M2 3h6a4 4 0 014 4v14a3 3 0 00-3-3H2z"/><path d="M22 3h-6a4 4 0 00-4 4v14a3 3 0 013-3h7z"/></svg>
              Readability: <strong>${blog.readability_score || 'N/A'}</strong>
            </div>
          </div>
          <h2 class="blog-title">${escapeHtml(blog.title || 'Untitled Blog Post')}</h2>
          <p class="blog-description">${escapeHtml(blog.meta_description || '')}</p>
          ${sections.map(section => `
            <div class="blog-section">
              <h3 class="blog-section-heading">${escapeHtml(section.heading || '')}</h3>
              <div class="blog-section-content">${escapeHtml(section.content || '')}</div>
            </div>
          `).join('')}
        </div>
      </div>
    </div>
  `;
}

// ---------- Social Media Tab ----------
function renderSocialTab(social) {
  const linkedinHashtags = (social.linkedin_hashtags || []).map(h => `<span class="hashtag">${escapeHtml(h)}</span>`).join('');
  const twitterHashtags = (social.twitter_hashtags || []).map(h => `<span class="hashtag">${escapeHtml(h)}</span>`).join('');
  const instagramHashtags = (social.instagram_hashtags || []).map(h => `<span class="hashtag">${escapeHtml(h)}</span>`).join('');
  const twitterThread = social.twitter_thread || [];

  DOM.tabSocial.innerHTML = `
    <div class="result-card">
      <div class="result-card-header">
        <h3>
          <svg viewBox="0 0 24 24"><path d="M18 8h1a4 4 0 010 8h-1"/><path d="M2 8h16v9a4 4 0 01-4 4H6a4 4 0 01-4-4V8z"/></svg>
          Social Media Content
        </h3>
        <button class="copy-btn" onclick="copyToClipboard('social-content')" aria-label="Copy social media content">
          <svg viewBox="0 0 24 24"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>
          Copy
        </button>
      </div>
      <div class="result-card-body" id="social-content">
        <div class="social-grid">
          <!-- LinkedIn -->
          <div class="social-card social-linkedin">
            <div class="social-card-header">
              <svg viewBox="0 0 24 24"><path d="M16 8a6 6 0 016 6v7h-4v-7a2 2 0 00-2-2 2 2 0 00-2 2v7h-4v-7a6 6 0 016-6z"/><rect x="2" y="9" width="4" height="12"/><circle cx="4" cy="4" r="2"/></svg>
              LinkedIn Post
            </div>
            <div class="social-card-body">
              ${escapeHtml(social.linkedin_post || 'No LinkedIn post generated.')}
              ${linkedinHashtags ? `<div class="social-hashtags">${linkedinHashtags}</div>` : ''}
            </div>
          </div>

          <!-- Twitter / X -->
          <div class="social-card social-twitter">
            <div class="social-card-header">
              <svg viewBox="0 0 24 24"><path d="M23 3a10.9 10.9 0 01-3.14 1.53 4.48 4.48 0 00-7.86 3v1A10.66 10.66 0 013 4s-4 9 5 13a11.64 11.64 0 01-7 2c9 5 20 0 20-11.5a4.5 4.5 0 00-.08-.83A7.72 7.72 0 0023 3z"/></svg>
              Twitter/X Thread (${twitterThread.length} tweets)
            </div>
            <div class="social-card-body">
              <div class="twitter-thread">
                ${twitterThread.map((tweet, i) => `
                  <div class="thread-tweet">
                    <span class="thread-tweet-number">${i + 1}/${twitterThread.length}</span>
                    ${escapeHtml(tweet)}
                  </div>
                `).join('')}
              </div>
              ${twitterHashtags ? `<div class="social-hashtags">${twitterHashtags}</div>` : ''}
            </div>
          </div>

          <!-- Instagram -->
          <div class="social-card social-instagram">
            <div class="social-card-header">
              <svg viewBox="0 0 24 24"><rect x="2" y="2" width="20" height="20" rx="5" ry="5"/><path d="M16 11.37A4 4 0 1112.63 8 4 4 0 0116 11.37z"/><line x1="17.5" y1="6.5" x2="17.51" y2="6.5"/></svg>
              Instagram Caption
            </div>
            <div class="social-card-body">
              ${escapeHtml(social.instagram_caption || 'No Instagram caption generated.')}
              ${instagramHashtags ? `<div class="social-hashtags">${instagramHashtags}</div>` : ''}
            </div>
          </div>
        </div>
      </div>
    </div>
  `;
}

// ---------- Email Tab ----------
function renderEmailTab(email) {
  const subjectLines = email.subject_lines || [];
  const bodySections = email.body_sections || [];

  DOM.tabEmail.innerHTML = `
    <div class="result-card">
      <div class="result-card-header">
        <h3>
          <svg viewBox="0 0 24 24"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22 6 12 13 2 6"/></svg>
          Email Newsletter
        </h3>
        <button class="copy-btn" onclick="copyToClipboard('email-content')" aria-label="Copy email content">
          <svg viewBox="0 0 24 24"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>
          Copy
        </button>
      </div>
      <div class="result-card-body" id="email-content">
        <div class="email-preview">
          <!-- Subject Lines A/B -->
          <div>
            <h4 style="font-size:var(--font-size-sm);font-weight:700;color:var(--slate-700);margin-bottom:var(--space-3)">A/B Subject Line Options</h4>
            <div class="email-subject-lines">
              ${subjectLines.map((line, i) => `
                <div class="email-subject">
                  <span class="email-subject-label">Option ${String.fromCharCode(65 + i)}</span>
                  <span class="email-subject-text">${escapeHtml(line)}</span>
                </div>
              `).join('')}
            </div>
          </div>

          ${email.preview_text ? `
            <div class="blog-meta-item" style="display:inline-flex;margin-top:var(--space-2)">
              <svg viewBox="0 0 24 24"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
              Preview: <strong>${escapeHtml(email.preview_text)}</strong>
            </div>
          ` : ''}

          <!-- Email Body Preview -->
          <div class="email-body-preview">
            <h4>${escapeHtml(email.header || 'Newsletter')}</h4>
            ${bodySections.map(section => `
              <div class="email-section">
                <h5>${escapeHtml(section.heading || '')}</h5>
                <p>${escapeHtml(section.content || '')}</p>
              </div>
            `).join('')}
            ${email.cta_text ? `
              <a href="${escapeHtml(email.cta_url || '#')}" class="email-cta" target="_blank" rel="noopener">
                ${escapeHtml(email.cta_text)}
              </a>
            ` : ''}
          </div>
        </div>
      </div>
    </div>
  `;
}

// ---------- Ad Copy Tab ----------
function renderAdsTab(ads) {
  const meta = ads.meta_ad || {};
  const google = ads.google_ad || {};
  const googleHeadlines = google.headlines || [];
  const googleDescriptions = google.descriptions || [];

  DOM.tabAds.innerHTML = `
    <div class="result-card">
      <div class="result-card-header">
        <h3>
          <svg viewBox="0 0 24 24"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><line x1="3" y1="9" x2="21" y2="9"/></svg>
          Ad Copy
        </h3>
        <button class="copy-btn" onclick="copyToClipboard('ads-content')" aria-label="Copy ad copy">
          <svg viewBox="0 0 24 24"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>
          Copy
        </button>
      </div>
      <div class="result-card-body" id="ads-content">
        <div class="ad-grid">
          <!-- Meta Ad -->
          <div class="ad-card ad-meta">
            <div class="ad-card-header">
              <svg viewBox="0 0 24 24"><path d="M18 2h-3a5 5 0 00-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 011-1h3z"/></svg>
              Meta (Facebook/Instagram) Ad
            </div>
            <div class="ad-card-body">
              <div class="ad-field">
                <span class="ad-field-label">Headline</span>
                <span class="ad-field-value"><strong>${escapeHtml(meta.headline || '')}</strong></span>
              </div>
              <div class="ad-field">
                <span class="ad-field-label">Primary Text</span>
                <span class="ad-field-value">${escapeHtml(meta.primary_text || '')}</span>
              </div>
              <div class="ad-field">
                <span class="ad-field-label">Description</span>
                <span class="ad-field-value">${escapeHtml(meta.description || '')}</span>
              </div>
              <div class="ad-field">
                <span class="ad-field-label">CTA</span>
                <span class="ad-field-value"><strong>${escapeHtml(meta.cta || 'Learn More')}</strong></span>
              </div>
            </div>
          </div>

          <!-- Google Ad -->
          <div class="ad-card ad-google">
            <div class="ad-card-header">
              <svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
              Google Search Ad
            </div>
            <div class="ad-card-body">
              <div class="ad-field">
                <span class="ad-field-label">Headlines</span>
                ${googleHeadlines.map((h, i) => `
                  <span class="ad-field-value" style="padding:var(--space-1) 0;border-bottom:1px solid var(--slate-100)">
                    <strong>${i + 1}.</strong> ${escapeHtml(h)}
                  </span>
                `).join('')}
              </div>
              <div class="ad-field" style="margin-top:var(--space-3)">
                <span class="ad-field-label">Descriptions</span>
                ${googleDescriptions.map((d, i) => `
                  <span class="ad-field-value" style="padding:var(--space-1) 0">${escapeHtml(d)}</span>
                `).join('')}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  `;
}

// ---------- Analytics Tab ----------
function renderAnalyticsTab(analytics) {
  const metrics = [
    {
      label: 'Projected Blog Views',
      value: formatNumber(analytics.projected_blog_views || 0),
      icon: `<svg viewBox="0 0 24 24"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>`,
      bg: 'var(--primary-50)',
      color: 'var(--primary-500)',
      trend: '+12%',
      trendDir: 'up'
    },
    {
      label: 'Social Media Reach',
      value: formatNumber(analytics.projected_social_reach || 0),
      icon: `<svg viewBox="0 0 24 24"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87"/><path d="M16 3.13a4 4 0 010 7.75"/></svg>`,
      bg: 'var(--accent-50)',
      color: 'var(--accent-500)',
      trend: '+8%',
      trendDir: 'up'
    },
    {
      label: 'Email Open Rate',
      value: `${analytics.projected_email_open_rate || 0}%`,
      icon: `<svg viewBox="0 0 24 24"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22 6 12 13 2 6"/></svg>`,
      bg: 'var(--success-50)',
      color: 'var(--success-500)',
      trend: '+3%',
      trendDir: 'up'
    },
    {
      label: 'Projected CTR',
      value: `${analytics.projected_ctr || 0}%`,
      icon: `<svg viewBox="0 0 24 24"><path d="M10 13a5 5 0 007.54.54l3-3a5 5 0 00-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 00-7.54-.54l-3 3a5 5 0 007.07 7.07l1.71-1.71"/></svg>`,
      bg: 'var(--info-50)',
      color: 'var(--info-500)',
      trend: '+5%',
      trendDir: 'up'
    },
  ];

  const contentScore = analytics.overall_content_score || 0;

  DOM.tabAnalytics.innerHTML = `
    <div class="result-card">
      <div class="result-card-header">
        <h3>
          <svg viewBox="0 0 24 24"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>
          Content Analytics Predictions
        </h3>
      </div>
      <div class="result-card-body">
        <div class="analytics-grid">
          ${metrics.map(m => `
            <div class="metric-card">
              <div class="metric-icon" style="background:${m.bg}">
                <span style="color:${m.color}">${m.icon}</span>
              </div>
              <div class="metric-value">${m.value}</div>
              <div class="metric-label">${m.label}</div>
              <div class="metric-trend ${m.trendDir}">
                <svg viewBox="0 0 24 24"><polyline points="${m.trendDir === 'up' ? '23 6 13.5 15.5 8.5 10.5 1 18' : '23 18 13.5 8.5 8.5 13.5 1 6'}"/></svg>
                ${m.trend} vs industry avg
              </div>
            </div>
          `).join('')}
        </div>

        <!-- Content Score -->
        <div class="content-score-container">
          <div class="content-score-header">
            <h4>Overall Content Quality Score</h4>
            <span class="content-score-value">${contentScore}/100</span>
          </div>
          <div class="score-bar-track">
            <div class="score-bar-fill" style="width:0%" id="scoreBarFill"></div>
          </div>
          <p style="margin-top:var(--space-3);font-size:var(--font-size-xs);color:var(--slate-500)">
            Based on SEO optimization, readability, engagement potential, and brand alignment analysis.
          </p>
        </div>
      </div>
    </div>
  `;

  // Animate score bar
  requestAnimationFrame(() => {
    setTimeout(() => {
      const fill = document.getElementById('scoreBarFill');
      if (fill) fill.style.width = `${contentScore}%`;
    }, 100);
  });
}

// ============================================================
// TAB NAVIGATION
// ============================================================
function initTabNavigation() {
  DOM.resultsTabs.addEventListener('click', (e) => {
    const tab = e.target.closest('.results-tab');
    if (!tab) return;

    const tabKey = tab.dataset.tab;

    // Update tab buttons
    $$('.results-tab').forEach(t => {
      t.classList.remove('active');
      t.setAttribute('aria-selected', 'false');
    });
    tab.classList.add('active');
    tab.setAttribute('aria-selected', 'true');

    // Update tab panels
    $$('.tab-panel').forEach(p => p.classList.remove('active'));
    const panel = $(`#tab-${tabKey}`);
    if (panel) panel.classList.add('active');
  });
}

// ============================================================
// DOWNLOAD PDF
// ============================================================
function initDownloadButton() {
  DOM.downloadPdfBtn.addEventListener('click', () => {
    if (!currentJobId) {
      showToast('error', 'No Report', 'No report available to download.');
      return;
    }

    const link = document.createElement('a');
    link.href = `/report/${currentJobId}.pdf`;
    link.download = '';
    link.click();

    showToast('info', 'Downloading PDF', 'Your content marketing report is being downloaded.');
  });
}

// ============================================================
// NEW GENERATION
// ============================================================
function initNewGenerationButton() {
  DOM.newGenerationBtn.addEventListener('click', () => {
    DOM.resultsContainer.classList.add('hidden');
    DOM.welcomeState.classList.remove('hidden');
    currentJobId = null;

    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });
}

// ============================================================
// COPY TO CLIPBOARD
// ============================================================
async function copyToClipboard(elementId) {
  const el = document.getElementById(elementId);
  if (!el) return;

  try {
    const text = el.innerText || el.textContent;
    await navigator.clipboard.writeText(text);
    showToast('success', 'Copied!', 'Content copied to clipboard.');
  } catch (err) {
    // Fallback
    const range = document.createRange();
    range.selectNodeContents(el);
    const selection = window.getSelection();
    selection.removeAllRanges();
    selection.addRange(range);
    document.execCommand('copy');
    selection.removeAllRanges();
    showToast('success', 'Copied!', 'Content copied to clipboard.');
  }
}

window.copyToClipboard = copyToClipboard;

// ============================================================
// TOAST NOTIFICATIONS
// ============================================================
function showToast(type, title, message) {
  const icons = {
    success: `<svg class="toast-icon" viewBox="0 0 24 24"><path d="M22 11.08V12a10 10 0 11-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>`,
    error:   `<svg class="toast-icon" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>`,
    info:    `<svg class="toast-icon" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>`,
  };

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `
    ${icons[type] || icons.info}
    <div class="toast-content">
      <div class="toast-title">${escapeHtml(title)}</div>
      ${message ? `<div class="toast-message">${escapeHtml(message)}</div>` : ''}
    </div>
    <button class="toast-close" aria-label="Dismiss notification">
      <svg viewBox="0 0 24 24"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
    </button>
  `;

  DOM.toastContainer.appendChild(toast);

  // Close button
  toast.querySelector('.toast-close').addEventListener('click', () => {
    dismissToast(toast);
  });

  // Auto dismiss after 5s
  setTimeout(() => dismissToast(toast), 5000);
}

function dismissToast(toast) {
  if (!toast || !toast.parentNode) return;
  toast.classList.add('removing');
  setTimeout(() => {
    if (toast.parentNode) toast.parentNode.removeChild(toast);
  }, 200);
}

// ============================================================
// UTILITIES
// ============================================================
function escapeHtml(str) {
  if (!str) return '';
  const div = document.createElement('div');
  div.textContent = String(str);
  return div.innerHTML;
}

function formatNumber(num) {
  if (typeof num !== 'number') num = parseInt(num) || 0;
  if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
  if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
  return num.toLocaleString();
}

function getDifficultyClass(score) {
  if (score <= 33) return 'easy';
  if (score <= 66) return 'medium';
  return 'hard';
}
