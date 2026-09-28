/**
 * ResqOps Frontend Application
 * Handles live telemetry simulation, dual-agent comparison,
 * and Hindsight memory bank exploration and retention.
 */

// State
let currentScenarios = {};
let currentMemories = [];

// DOM Elements
const inputService = document.getElementById('input-service');
const inputSeverity = document.getElementById('input-severity');
const inputAlertName = document.getElementById('input-alert-name');
const inputSummary = document.getElementById('input-summary');
const inputRawLogs = document.getElementById('input-raw-logs');
const badgeSeverity = document.getElementById('badge-severity');

const btnInvestigate = document.getElementById('btn-investigate');
const spinnerInvestigate = document.getElementById('spinner-investigate');
const btnInvestigateText = document.getElementById('btn-investigate-text');

const vanillaDiagnosis = document.getElementById('vanilla-diagnosis');
const vanillaConfidence = document.getElementById('vanilla-confidence');
const vanillaMttr = document.getElementById('vanilla-mttr');

const hindsightDiagnosis = document.getElementById('hindsight-diagnosis');
const hindsightConfidence = document.getElementById('hindsight-confidence');
const hindsightMttr = document.getElementById('hindsight-mttr');
const matchedIncidentBadges = document.getElementById('matched-incident-badges');

const hindsightModeText = document.getElementById('hindsight-mode-text');
const memoryCounter = document.getElementById('memory-counter');
const tabCountBadge = document.getElementById('tab-count-badge');
const memoryCardsContainer = document.getElementById('memory-cards-container');
const inputSearchMemory = document.getElementById('input-search-memory');

// Tab Buttons
const tabBtnMemories = document.getElementById('tab-btn-memories');
const tabBtnRetain = document.getElementById('tab-btn-retain');
const tabContentMemories = document.getElementById('tab-content-memories');
const tabContentRetain = document.getElementById('tab-content-retain');

// Retain Form
const retainForm = document.getElementById('retain-form');
const retainService = document.getElementById('retain-service');
const retainTitle = document.getElementById('retain-title');
const retainResolution = document.getElementById('retain-resolution');
const retainFailed = document.getElementById('retain-failed');

// Settings Modal
const settingsModal = document.getElementById('settings-modal');
const btnOpenSettings = document.getElementById('btn-open-settings');
const btnCloseSettings = document.getElementById('btn-close-settings');
const btnCancelSettings = document.getElementById('btn-cancel-settings');
const settingsForm = document.getElementById('settings-form');

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
  setupEventListeners();
  await loadStatus();
  await loadScenarios();
  await loadMemories();
});

function setupEventListeners() {
  // Scenario button clicks
  document.querySelectorAll('.scenario-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const scenarioKey = btn.dataset.scenario;
      loadScenarioIntoForm(scenarioKey);
    });
  });

  // Severity change badge update
  inputSeverity.addEventListener('change', () => {
    updateSeverityBadge(inputSeverity.value);
  });

  // Investigate form submit
  document.getElementById('incident-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    await runInvestigation();
  });

  // Tabs switching
  tabBtnMemories.addEventListener('click', () => switchTab('memories'));
  tabBtnRetain.addEventListener('click', () => switchTab('retain'));

  // Search memories
  inputSearchMemory.addEventListener('input', (e) => {
    filterMemoryCards(e.target.value);
  });

  // Refresh memories button
  document.getElementById('btn-refresh-memories').addEventListener('click', loadMemories);

  // Retain post-mortem submit
  retainForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    await submitPostMortem();
  });

  // Reset memory button
  document.getElementById('btn-reset-memory').addEventListener('click', async () => {
    if (confirm('Reset memory bank to original institutional post-mortems?')) {
      const res = await fetch('/api/memories/reset', { method: 'POST' });
      if (res.ok) {
        await loadMemories();
        await loadStatus();
        alert('Hindsight Memory Bank reset to original institutional baseline.');
      }
    }
  });

  // Settings modal
  btnOpenSettings.addEventListener('click', () => settingsModal.classList.remove('hidden'));
  btnCloseSettings.addEventListener('click', () => settingsModal.classList.add('hidden'));
  btnCancelSettings.addEventListener('click', () => settingsModal.classList.add('hidden'));

  settingsForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const payload = {
      hindsight_api_key: document.getElementById('set-hindsight-key').value,
      hindsight_base_url: document.getElementById('set-hindsight-url').value,
      hindsight_bank_id: document.getElementById('set-hindsight-bank').value,
      groq_api_key: document.getElementById('set-groq-key').value,
      gemini_api_key: document.getElementById('set-gemini-key').value
    };

    try {
      const res = await fetch('/api/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        settingsModal.classList.add('hidden');
        await loadStatus();
        alert('Settings updated successfully!');
      }
    } catch (err) {
      alert('Error updating settings: ' + err);
    }
  });
}

function updateSeverityBadge(sev) {
  badgeSeverity.textContent = `${sev} - ${sev === 'P0' ? 'OUTAGE BLOCK' : (sev === 'P1' ? 'CRITICAL DEGRADE' : 'MODERATE')}`;
  badgeSeverity.className = 'text-xs px-2 py-0.5 rounded font-mono font-bold ';
  if (sev === 'P0') {
    badgeSeverity.className += 'bg-red-950 text-red-400 border border-red-800';
  } else if (sev === 'P1') {
    badgeSeverity.className += 'bg-orange-950 text-orange-400 border border-orange-800';
  } else {
    badgeSeverity.className += 'bg-yellow-950 text-yellow-400 border border-yellow-800';
  }
}

async function loadStatus() {
  try {
    const res = await fetch('/api/status');
    const data = await res.json();
    if (data.hindsight) {
      hindsightModeText.textContent = data.hindsight.mode === 'cloud' ? 'Cloud (Vectorize)' : 'Local Bank';
      hindsightModeText.className = data.hindsight.mode === 'cloud' ? 'text-cyan-400 font-bold' : 'text-emerald-400 font-semibold';
      memoryCounter.textContent = `${data.hindsight.total_memories} Post-Mortems`;
      tabCountBadge.textContent = data.hindsight.total_memories;
    }
  } catch (e) {
    console.error('Failed to load status:', e);
  }
}

async function loadScenarios() {
  try {
    const res = await fetch('/api/scenarios');
    currentScenarios = await res.json();
  } catch (e) {
    console.error('Failed to load scenarios:', e);
  }
}

function loadScenarioIntoForm(key) {
  const scn = currentScenarios[key];
  if (!scn) return;

  inputService.value = scn.service;
  inputSeverity.value = scn.severity;
  updateSeverityBadge(scn.severity);
  inputAlertName.value = scn.alert_name;
  inputSummary.value = scn.summary;
  inputRawLogs.value = scn.raw_logs;

  // If this is the novel incident, populate retain form with prepopulated draft
  if (key === 'novel_rabbitmq_poison_pill') {
    retainService.value = scn.service;
    retainTitle.value = "RabbitMQ Dead-Letter Queue Flooding & Unhandled JSON Schema";
    retainResolution.value = "Configured Jackson ObjectMapper with @JsonIgnoreProperties(ignoreUnknown = true) to prevent unhandled schema property crashes. Replayed 850k DLQ messages via rabbitmqctl shovel and scaled workers to 12 replicas.";
    retainFailed.value = "Purging the entire RabbitMQ queue lost unacknowledged user emails. Restarting workers without the Jackson patch caused immediate crash loops.";
  }

  // Visual highlight
  document.querySelectorAll('.scenario-btn').forEach(btn => {
    if (btn.dataset.scenario === key) {
      btn.classList.add('ring-2', 'ring-cyan-400');
    } else {
      btn.classList.remove('ring-2', 'ring-cyan-400');
    }
  });
}

async function runInvestigation() {
  const payload = {
    service: inputService.value,
    severity: inputSeverity.value,
    alert_name: inputAlertName.value,
    summary: inputSummary.value,
    raw_logs: inputRawLogs.value
  };

  // UI loading state
  spinnerInvestigate.classList.remove('hidden');
  btnInvestigateText.textContent = "Querying Hindsight & Running Dual Diagnosis...";
  btnInvestigate.disabled = true;

  try {
    const res = await fetch('/api/investigate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    
    if (!res.ok) {
      throw new Error(`Server returned ${res.status}`);
    }

    const data = await res.json();
    renderInvestigationResults(data);
  } catch (err) {
    alert("Investigation error: " + err.message);
  } finally {
    spinnerInvestigate.classList.add('hidden');
    btnInvestigateText.textContent = "⚡ Trigger Dual-Agent Investigation";
    btnInvestigate.disabled = false;
  }
}

function renderInvestigationResults(data) {
  const v = data.vanilla_agent;
  const h = data.hindsight_agent;

  // Stateless Vanilla results
  vanillaConfidence.textContent = `${v.confidence_score}%`;
  vanillaMttr.textContent = v.mttr_estimate;
  vanillaDiagnosis.innerHTML = formatMarkdown(v.diagnosis);

  // Hindsight Memory-augmented results
  hindsightConfidence.textContent = `${h.confidence_score}%`;
  hindsightMttr.textContent = h.mttr_estimate;
  hindsightDiagnosis.innerHTML = formatMarkdown(h.diagnosis);

  // Render matched incident badges
  matchedIncidentBadges.innerHTML = '<span class="text-cyan-400 font-mono text-[10px]">Institutional match:</span>';
  if (h.matched_incidents && h.matched_incidents.length > 0) {
    h.matched_incidents.forEach(id => {
      const badge = document.createElement('span');
      badge.className = 'px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 font-mono text-[10px] border border-cyan-800 animate-pulse';
      badge.textContent = id;
      matchedIncidentBadges.appendChild(badge);
    });
  } else {
    const badge = document.createElement('span');
    badge.className = 'px-2 py-0.5 rounded bg-amber-950 text-amber-300 font-mono text-[10px] border border-amber-800';
    badge.textContent = 'NOVEL - Learn via Retain Tab';
    matchedIncidentBadges.appendChild(badge);
  }
}

async function loadMemories() {
  try {
    const res = await fetch('/api/memories');
    const data = await res.json();
    currentMemories = data.memories || [];
    renderMemoryCards(currentMemories);
    memoryCounter.textContent = `${currentMemories.length} Post-Mortems`;
    tabCountBadge.textContent = currentMemories.length;
  } catch (e) {
    console.error('Failed to load memories:', e);
  }
}

function renderMemoryCards(memories) {
  memoryCardsContainer.innerHTML = '';

  if (memories.length === 0) {
    memoryCardsContainer.innerHTML = '<p class="text-gray-500 text-xs italic text-center py-6">No memories retained in this bank yet.</p>';
    return;
  }

  memories.forEach(mem => {
    const meta = mem.metadata || {};
    const card = document.createElement('div');
    card.className = 'bg-sredark border border-gray-800 hover:border-cyan-800/80 rounded-lg p-3 text-xs transition space-y-2';

    const tagsHtml = (mem.tags || []).map(t => `<span class="px-1.5 py-0.5 rounded bg-gray-800 text-gray-400 font-mono text-[9px] border border-gray-700">#${t}</span>`).join(' ');

    card.innerHTML = `
      <div class="flex items-center justify-between">
        <div class="flex items-center space-x-2">
          <span class="font-mono font-bold text-cyan-400">${meta.incident_id || mem.id}</span>
          <span class="text-gray-400 font-mono text-[10px]">${meta.service || 'infrastructure'}</span>
          <span class="px-1.5 py-0.2 rounded font-mono text-[9px] ${meta.severity === 'P0' ? 'bg-red-950 text-red-400 border border-red-800' : 'bg-orange-950 text-orange-400 border border-orange-800'}">${meta.severity || 'P1'}</span>
        </div>
        <span class="text-[10px] text-gray-500 font-mono">${mem.timestamp ? mem.timestamp.split('T')[0] : ''}</span>
      </div>
      <div class="text-gray-300 font-medium">
        ${meta.root_cause || (mem.content ? mem.content.substring(0, 160) + '...' : '')}
      </div>
      <div class="flex flex-wrap gap-1 pt-1">
        ${tagsHtml}
      </div>
    `;

    memoryCardsContainer.appendChild(card);
  });
}

function filterMemoryCards(query) {
  if (!query) {
    renderMemoryCards(currentMemories);
    return;
  }
  const q = query.toLowerCase();
  const filtered = currentMemories.filter(m => {
    return JSON.stringify(m).toLowerCase().includes(q);
  });
  renderMemoryCards(filtered);
}

function switchTab(tab) {
  if (tab === 'memories') {
    tabBtnMemories.className = 'px-4 py-2 text-xs font-semibold uppercase tracking-wider text-cyan-400 border-b-2 border-cyan-400 transition flex items-center space-x-1.5';
    tabBtnRetain.className = 'px-4 py-2 text-xs font-semibold uppercase tracking-wider text-gray-400 hover:text-gray-200 border-b-2 border-transparent transition flex items-center space-x-1.5';
    tabContentMemories.classList.remove('hidden');
    tabContentRetain.classList.add('hidden');
  } else {
    tabBtnRetain.className = 'px-4 py-2 text-xs font-semibold uppercase tracking-wider text-emerald-400 border-b-2 border-emerald-400 transition flex items-center space-x-1.5';
    tabBtnMemories.className = 'px-4 py-2 text-xs font-semibold uppercase tracking-wider text-gray-400 hover:text-gray-200 border-b-2 border-transparent transition flex items-center space-x-1.5';
    tabContentRetain.classList.remove('hidden');
    tabContentMemories.classList.add('hidden');
  }
}

async function submitPostMortem() {
  const payload = {
    service: retainService.value,
    title: retainTitle.value,
    severity: "P2",
    summary: "Dead-letter queue surge due to unhandled JSON schema field in notification dispatcher.",
    raw_logs: inputRawLogs.value,
    resolution_notes: retainResolution.value,
    failed_attempts_notes: retainFailed.value
  };

  try {
    const res = await fetch('/api/postmortem/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!res.ok) throw new Error(`HTTP ${res.status}`);

    const data = await res.json();
    alert(`🎉 Successfully Synthesized & Retained in Hindsight!\n\nIncident ID: ${data.post_mortem.id}\nMemory Bank now has ${data.total_memories} post-mortems.\n\nNow, re-trigger the investigation on this alert and watch ResqOps instantly recall this solution!`);

    await loadMemories();
    await loadStatus();
    switchTab('memories');
  } catch (err) {
    alert('Failed to retain post-mortem: ' + err.message);
  }
}

// Markdown Formatter Utility
function formatMarkdown(text) {
  if (!text) return '';
  let html = text
    .replace(/^### (.*$)/gim, '<h3 class="text-sm font-bold text-white mt-2 mb-1">$1</h3>')
    .replace(/^## (.*$)/gim, '<h2 class="text-sm font-bold text-white mt-3 mb-1">$1</h2>')
    .replace(/^# (.*$)/gim, '<h1 class="text-base font-bold text-white mt-3 mb-1">$1</h1>')
    .replace(/\*\*(.*?)\*\*/gim, '<strong class="text-white">$1</strong>')
    .replace(/\*(.*?)\*/gim, '<em class="text-gray-300">$1</em>')
    .replace(/```bash([\s\S]*?)```/gim, '<pre class="bg-black/80 text-cyan-300 p-2.5 rounded font-mono text-[11px] my-2 border border-gray-800 overflow-x-auto">$1</pre>')
    .replace(/```([\s\S]*?)```/gim, '<pre class="bg-black/80 text-emerald-300 p-2.5 rounded font-mono text-[11px] my-2 border border-gray-800 overflow-x-auto">$1</pre>')
    .replace(/`([^`]+)`/gim, '<code class="bg-gray-800 text-cyan-300 px-1 py-0.5 rounded font-mono text-[11px]">$1</code>')
    .replace(/^\s*-\s+(.*$)/gim, '<li class="ml-4 list-disc text-gray-300 my-0.5">$1</li>')
    .replace(/\n/gim, '<br>');
  return `<div class="diagnosis-container">${html}</div>`;
}
