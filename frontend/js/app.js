/* ===================================================================
   FraudIntel Dashboard — Main Application Logic
   =================================================================== */

/* --- Global functions for floating Command Center chatbot --- */
function toggleCommandCenter() {
  const panel = document.getElementById('cc-panel');
  const fab = document.getElementById('cc-fab');
  if (!panel || !fab) return;
  const isOpen = panel.classList.toggle('open');
  fab.classList.toggle('open', isOpen);
  if (isOpen) {
    const input = document.getElementById('mission-input');
    if (input) setTimeout(() => input.focus(), 300);
  }
}

function clearMissionLog() {
  const log = document.getElementById('mission-log');
  if (!log) return;
  log.innerHTML = `
    <div class="cc-welcome">
      <div class="cc-welcome-icon"><i class="fas fa-shield-alt"></i></div>
      <div class="cc-welcome-title">FRAUDINTEL AI INVESTIGATOR</div>
      <div class="cc-welcome-sub">Ask me to investigate accounts, analyze fraud patterns, or run threat intelligence.</div>
      <div class="cc-quick-actions">
        <button class="cc-quick-btn" onclick="quickMission('Investigate ACC-001')"><i class="fas fa-search"></i> Investigate ACC-001</button>
        <button class="cc-quick-btn" onclick="quickMission('Analyze emerging fraud trends')"><i class="fas fa-chart-line"></i> Fraud trends</button>
        <button class="cc-quick-btn" onclick="quickMission('Show high risk accounts')"><i class="fas fa-exclamation-triangle"></i> High risk accounts</button>
      </div>
    </div>
  `;
  // Reset agent pills
  document.querySelectorAll('.cc-agents-bar .agent-status').forEach(el => {
    el.classList.remove('active', 'complete');
  });
}

function quickMission(text) {
  const input = document.getElementById('mission-input');
  if (!input) return;
  input.value = text;
  // Trigger the execute click
  const btn = document.getElementById('btn-execute-mission');
  if (btn) btn.click();
}

(() => {
  "use strict";

  // -----------------------------------------------------------------
  // 1. API Helper
  // -----------------------------------------------------------------
  const BASE_URL = '';
  const API = {
    async get(url) {
      if (url.startsWith('/')) url = BASE_URL + url;
      try {
        const res = await fetch(url, {
          headers: { "X-API-Key": "fi-hackathon-2026-secret" }
        });
        if (!res.ok) {
          showGlobalError();
          throw new Error(`GET ${url} → ${res.status}`);
        }
        return await res.json();
      } catch (err) {
        showGlobalError();
        console.error("[API GET]", url, err);
        throw err;
      }
    },

    async post(url, body) {
      if (url.startsWith('/')) url = BASE_URL + url;
      try {
        const res = await fetch(url, {
          method: "POST",
          headers: { 
            "Content-Type": "application/json",
            "X-API-Key": "fi-hackathon-2026-secret"
          },
          body: JSON.stringify(body),
        });
        if (!res.ok) {
          showGlobalError();
          const detail = await res.json().catch(() => ({}));
          throw new Error(detail.detail || `POST ${url} → ${res.status}`);
        }
        return await res.json();
      } catch (err) {
        showGlobalError();
        console.error("[API POST]", url, err);
        throw err;
      }
    },
  };

  // Currently selected case
  let selectedCaseId = null;
  let refreshInterval = null;
  let allCases = [];

  function showGlobalError() {
    const banner = document.getElementById("global-error-banner");
    if (banner) banner.classList.remove("hidden");
  }

  // -----------------------------------------------------------------
  // 2. initDashboard
  // -----------------------------------------------------------------
  async function initDashboard() {
    // Start data loading concurrently
    const dataPromise = Promise.allSettled([loadStats(), loadCases(), loadAlerts()]);

    const intro = document.getElementById("cinematic-intro");
    if (!intro) {
      await dataPromise;
      startRefresh();
      return;
    }

    let skip = false;
    const skipBtn = document.getElementById("skip-intro-btn");
    if (skipBtn) {
      skipBtn.addEventListener("click", () => {
        if (skip) return;
        skip = true;
        finishIntro(intro);
      });
    }

    const showScreen = async (id, duration) => {
      if (skip) return;
      const screen = document.getElementById(id);
      if (screen) screen.classList.add("active");
      
      // We implement a breakable sleep loop so Skip feels instant
      const intervals = duration / 100;
      for (let i = 0; i < intervals; i++) {
        if (skip) break;
        await sleep(100);
      }

      if (screen) screen.classList.remove("active");
    };

    // SCREEN 1
    if (!skip) await showScreen("intro-screen-1", 2000);
    // SCREEN 2
    if (!skip) await showScreen("intro-screen-2", 3000);
    // SCREEN 3
    if (!skip) await showScreen("intro-screen-3", 2500);
    
    // SCREEN 4
    if (!skip) {
      const screen4 = document.getElementById("intro-screen-4");
      if (screen4) screen4.classList.add("active");
      for (let i = 1; i <= 6; i++) {
        if (skip) break;
        const li = document.getElementById(`agent-li-${i}`);
        if (li) li.classList.add("visible");
        await sleep(500);
      }
      for (let i = 0; i < 15; i++) { if (skip) break; await sleep(100); }
      if (screen4) screen4.classList.remove("active");
    }

    // SCREEN 5
    if (!skip) {
      const screen5 = document.getElementById("intro-screen-5");
      if (screen5) screen5.classList.add("active");
      
      const msgs = [
        "Preparing mission protocols...",
        "Connecting transactions...",
        "Mapping hidden relationships...",
        "Reconstructing timeline...",
        "Validating compliance rules...",
        "Activating proactive hunting..."
      ];
      const statusEl = document.getElementById("loading-micro-status");

      for (let i = 1; i <= 6; i++) {
        if (skip) break;
        const step = document.getElementById(`step-${i}`);
        if (step) step.classList.add("active");
        if (statusEl) statusEl.textContent = msgs[i-1] || "Finalizing...";
        for (let j = 0; j < 6; j++) { if (skip) break; await sleep(100); }
        if (step) {
          step.classList.remove("active");
          step.classList.add("done");
        }
      }
      
      // Wait for data load to actually finish just in case
      await dataPromise;
      
      for (let j = 0; j < 5; j++) { if (skip) break; await sleep(100); }
      if (screen5) screen5.classList.remove("active");
    }

    // SCREEN 6
    if (!skip) {
      const screen6 = document.getElementById("intro-screen-6");
      if (screen6) screen6.classList.add("active");
      for (let j = 0; j < 30; j++) { if (skip) break; await sleep(100); }
    }

    if (!skip) {
      finishIntro(intro);
    }

    startRefresh();
  }

  function finishIntro(introContainer) {
    if (introContainer) {
      introContainer.classList.add("zoom-fade-out");
      setTimeout(() => introContainer.remove(), 1500);
    }
  }

  function startRefresh() {
    if (refreshInterval) clearInterval(refreshInterval);
    refreshInterval = setInterval(() => {
      loadStats();
      loadAlerts();
    }, 30000);
  }

  // -----------------------------------------------------------------
  // 3. loadStats
  // -----------------------------------------------------------------
  async function loadStats() {
    try {
      const stats = await API.get("/api/dashboard/stats");

      setValue("stat-active-cases", stats.active_investigations ?? 0);
      setValue("stat-pending-alerts", stats.pending_alerts ?? 0);
      setValue("stat-high-risk", stats.high_risk_cases ?? 0);
      setValue("stat-avg-score", stats.avg_fraud_score != null
        ? Math.round(stats.avg_fraud_score)
        : 0);
    } catch {
      // leave current values
    }
  }

  function setValue(cardId, value) {
    const card = document.getElementById(cardId);
    if (!card) return;
    const el = card.querySelector(".stat-value");
    if (el) el.textContent = value;
  }

  // -----------------------------------------------------------------
  // 4. loadCases
  // -----------------------------------------------------------------
  async function loadCases() {
    try {
      allCases = await API.get("/api/cases");
      filterAndRenderCases();
    } catch {
      // silent
    }
  }

  function filterAndRenderCases() {
    const searchInput = document.getElementById("search-input");
    const term = searchInput ? searchInput.value.toLowerCase() : "";
    let filtered = allCases;
    if (term) {
      filtered = allCases.filter(c => 
        (c.case_id && c.case_id.toLowerCase().includes(term)) ||
        (c.executive_summary && c.executive_summary.toLowerCase().includes(term)) ||
        (c.classification && c.classification.toLowerCase().includes(term))
      );
    }
    renderCaseQueue(filtered);
  }

  // -----------------------------------------------------------------
  // 5. renderCaseQueue
  // -----------------------------------------------------------------
  function renderCaseQueue(cases) {
    const queue = document.getElementById("case-queue");
    if (!queue) return;

    if (!cases || cases.length === 0) {
      queue.innerHTML = `
        <div class="empty-state">
          <div class="empty-state-icon"><i class="fas fa-folder-open"></i></div>
          <div class="empty-state-text">No cases yet.<br>Start an investigation to begin.</div>
        </div>`;
      return;
    }

    queue.innerHTML = cases.map((c) => {
      const score = c.fraud_score ?? 0;
      let riskClass = "risk-low";
      if (score >= 70) riskClass = "risk-high";
      else if (score >= 40) riskClass = "risk-medium";
      
      const status = c.status ? formatStatus(c.status) : "Unknown";

      return `
        <div class="case-card ${riskClass} ${c.case_id === selectedCaseId ? "active" : ""}"
             data-case-id="${c.case_id}" role="listitem">
          <div class="case-card-header">
            <span class="case-card-id">${c.case_id}</span>
            <span class="risk-pill ${riskClass}">${score}</span>
          </div>
          <div class="case-card-title">${truncate(c.executive_summary || c.classification || "", 80)}</div>
          <div class="case-card-meta">
            <span class="status-badge ${status.replace(/ /g, "_")}">${status}</span>
            <span>${c.updated_at ? formatTimeAgo(c.updated_at) : ""}</span>
          </div>
        </div>`;
    }).join("");

    // Click handlers
    queue.querySelectorAll(".case-card").forEach((card) => {
      card.addEventListener("click", () => {
        selectCase(card.dataset.caseId);
      });
    });
  }

  // -----------------------------------------------------------------
  // 6. selectCase
  // -----------------------------------------------------------------
  function selectCase(caseId) {
    selectedCaseId = caseId;

    // Highlight in sidebar
    document.querySelectorAll(".case-card").forEach((card) => {
      card.classList.toggle("active", card.dataset.caseId === caseId);
    });

    loadCaseDetail(caseId);
  }

  // -----------------------------------------------------------------
  // 7. loadCaseDetail
  // -----------------------------------------------------------------
  async function loadCaseDetail(caseId) {
    try {
      const caseData = await API.get(`/api/cases/${caseId}`);

      // Report tab
      renderReport(caseData);

      // SAR tab
      renderSAR(caseData.sar_draft);

      // Network tab — prioritize the network_map stored with the case
      if (caseData.network_map && caseData.network_map.nodes && caseData.network_map.nodes.length > 0) {
        renderNetworkGraph(caseData.network_map);
      } else {
        const entityId = extractEntityId(caseData);
        if (entityId) {
          try {
            const networkData = await API.get(`/api/network/${entityId}`);
            renderNetworkGraph(networkData);
          } catch {
            const container = document.getElementById("network-graph");
            if (container) container.innerHTML = '<div class="empty-state"><div class="empty-state-icon">🕸️</div><div class="empty-state-text">Network data unavailable</div></div>';
          }
        } else {
          const container = document.getElementById("network-graph");
          if (container) container.innerHTML = '<div class="empty-state"><div class="empty-state-icon">🕸️</div><div class="empty-state-text">No network data for this case</div></div>';
        }
      }

      // Timeline tab
      try {
        const events = await API.get(`/api/timeline/${caseId}`);
        renderTimeline(events);
      } catch {
        setPlaceholder("investigation-timeline", "Timeline data unavailable");
      }

      // Activate network tab
      activateTab("network");

    } catch (err) {
      showToast(`Failed to load case ${caseId}`, "error");
    }
  }

  function extractEntityId(caseData) {
    // Try to find an account ID from various fields
    if (caseData.evidence_collected) {
      const ev = caseData.evidence_collected;
      if (ev.customer && ev.customer.accounts && ev.customer.accounts[0]) {
        return ev.customer.accounts[0];
      }
      if (ev.transactions && ev.transactions[0] && ev.transactions[0].account_id) {
        return ev.transactions[0].account_id;
      }
    }
    // Try network_map
    if (caseData.network_map && caseData.network_map.nodes && caseData.network_map.nodes[0]) {
      return caseData.network_map.nodes[0].id;
    }
    // Fallback: parse from case key findings
    const accMatch = JSON.stringify(caseData).match(/ACC-\d{3}/);
    return accMatch ? accMatch[0] : null;
  }

  // -----------------------------------------------------------------
  // 8. renderNetworkGraph
  // -----------------------------------------------------------------
  let networkGraphInstance = null;

  function renderNetworkGraph(graphData) {
    const container = document.getElementById("network-graph");
    if (!container) return;

    if (!graphData || !graphData.nodes || graphData.nodes.length === 0) {
      container.innerHTML = '<div class="empty-state"><div class="empty-state-icon">🕸️</div><div class="empty-state-text">No network data available</div></div>';
      return;
    }

    // Clear placeholder text if it's there
    if (container.querySelector('.empty-state')) {
      container.innerHTML = '';
    }

    try {
      /* global FraudNetworkGraph */
      if (typeof FraudNetworkGraph !== "undefined") {
        if (!networkGraphInstance) {
          networkGraphInstance = new FraudNetworkGraph("network-graph");
        }
        networkGraphInstance.render(graphData);
      } else {
        // Fallback: simple summary
        container.innerHTML = `
          <div class="empty-state">
            <div class="empty-state-icon">🕸️</div>
            <div class="empty-state-text">
              Network: ${graphData.nodes.length} nodes, ${graphData.edges.length} edges
            </div>
          </div>`;
      }
    } catch (err) {
      console.error("Network graph render error:", err);
      container.innerHTML = '<div class="empty-state"><div class="empty-state-text">Error rendering network graph</div></div>';
    }
  }

  // -----------------------------------------------------------------
  // 9. renderTimeline
  // -----------------------------------------------------------------
  function renderTimeline(events) {
    const container = document.getElementById("investigation-timeline");
    if (!container) return;

    if (!events || events.length === 0) {
      container.innerHTML = '<div class="empty-state"><div class="empty-state-icon"><i class="fas fa-calendar-alt"></i></div><div class="empty-state-text">No timeline events</div></div>';
      return;
    }

    const html = `
      <div class="timeline-container">
        ${events.map((ev, i) => {
          const sev = ev.severity || "info";
          const typeClass = ev.event_type || "transaction";
          return `
            <div class="timeline-entry severity-${sev}" style="animation-delay: ${i * 0.05}s">
              <div class="timeline-card">
                <div class="timeline-time">${formatDateTime(ev.timestamp)}</div>
                <div class="timeline-desc">
                  <span class="timeline-type ${typeClass}">${ev.event_type || ""}</span>
                  ${escapeHtml(ev.description || "")}
                </div>
              </div>
            </div>`;
        }).join("")}
      </div>`;

    container.innerHTML = html;
  }

  // -----------------------------------------------------------------
  // 10. renderReport
  // -----------------------------------------------------------------
  function renderReport(caseData) {
    const container = document.getElementById("investigation-report");
    if (!container) return;

    const score = caseData.fraud_score ?? 0;
    const classification = caseData.classification || "unknown";
    
    let riskClass = "risk-low";
    if (score >= 70) riskClass = "risk-high";
    else if (score >= 40) riskClass = "risk-medium";
    
    const pillClass = riskClass;
    const scoreColor = score >= 70 ? "var(--accent-red)" : (score >= 40 ? "#ff9999" : "#ffffff");
    const confidence = caseData.confidence_level || "N/A";
    const summary = caseData.executive_summary || "No summary available.";
    const findings = caseData.key_findings || [];
    const indicators = caseData.fraud_indicators || [];
    const actions = caseData.recommended_actions || [];

    container.innerHTML = `
      <div class="report-container">

        <!-- Score Banner -->
        <div class="report-score-banner">
          <div class="report-score-number ${pillClass}">${score}</div>
          <div class="report-score-meta">
            <div class="report-score-class" style="color: ${scoreColor}">
              ${classification.replace(/_/g, " ").toUpperCase()}
            </div>
            <div class="report-score-confidence">Confidence: ${confidence}</div>
          </div>
          <div style="flex:1"></div>
          <div style="display: flex; flex-direction: column; align-items: flex-end; gap: 8px;">
            <div style="width:180px;height:8px;background:rgba(255,255,255,0.06);border-radius:4px;overflow:hidden;">
              <div style="width:${score}%;height:100%;background:${scoreColor};border-radius:4px;transition:width 0.8s ease;"></div>
            </div>
            <button id="btn-why-score" class="btn-primary" style="padding: 4px 10px; font-size: 0.65rem; border: 1px solid rgba(255,255,255,0.2); background: transparent;"><i class="fas fa-question-circle"></i> WHY THIS SCORE?</button>
          </div>
        </div>

        <!-- Risk Breakdown Container (Hidden by default) -->
        <div id="risk-breakdown-container" class="report-section" style="display: none; background: rgba(178,0,0,0.05); border: 1px dashed var(--accent-red); margin-top: 10px;">
        </div>

        <!-- Executive Summary -->
        <div class="report-section">
          <h3><i class="fas fa-clipboard-list"></i> Executive Summary</h3>
          <p>${escapeHtml(summary)}</p>
        </div>

        <!-- Key Findings -->
        ${findings.length > 0 ? `
        <div class="report-section">
          <h3><i class="fas fa-search"></i> Key Findings</h3>
          <ul>${findings.map(f => `<li>${escapeHtml(f)}</li>`).join("")}</ul>
        </div>` : ""}

        <!-- Fraud Indicators -->
        ${indicators.length > 0 ? `
        <div class="report-section">
          <h3><i class="fas fa-exclamation-triangle"></i> Fraud Indicators</h3>
          <ul>${indicators.map(f => `<li>${escapeHtml(f)}</li>`).join("")}</ul>
        </div>` : ""}

        <!-- Recommended Actions -->
        ${actions.length > 0 ? `
        <div class="report-section recommendations">
          <h3><i class="fas fa-check-circle"></i> Recommended Actions</h3>
          <ul>${actions.map(a => `<li>${escapeHtml(a)}</li>`).join("")}</ul>
        </div>` : ""}

        <!-- Analyst Feedback Form -->
        <div class="report-section feedback-section" style="margin-top: 30px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 20px;">
          <h3><i class="fas fa-comment-dots"></i> Analyst Feedback</h3>
          <p style="font-size: 0.8rem; color: var(--text-muted); margin-bottom: 10px;">Your feedback recalibrates the AI's risk scoring model for future cases.</p>
          <div style="display: flex; gap: 10px; margin-bottom: 15px;">
            <select id="feedback-decision" style="background: var(--surface); color: var(--text); border: 1px solid rgba(255,255,255,0.1); padding: 8px; flex: 1;">
              <option value="">Select Final Determination...</option>
              <option value="confirmed_fraud">Confirmed Fraud (True Positive)</option>
              <option value="false_positive">Legitimate Activity (False Positive)</option>
            </select>
          </div>
          <textarea id="feedback-notes" rows="3" placeholder="Analyst reasoning..." style="width: 100%; background: var(--surface); color: var(--text); border: 1px solid rgba(255,255,255,0.1); padding: 8px; margin-bottom: 10px; resize: vertical;"></textarea>
          <button id="btn-submit-feedback" class="btn-primary" style="width: 100%;"><i class="fas fa-paper-plane"></i> SUBMIT FEEDBACK</button>
        </div>

      </div>`;

    // Wire up the feedback submit button
    const submitBtn = document.getElementById("btn-submit-feedback");
    if (submitBtn) {
      submitBtn.addEventListener("click", async () => {
        const decision = document.getElementById("feedback-decision").value;
        const notes = document.getElementById("feedback-notes").value;
        if (!decision) {
          alert("Please select a final determination.");
          return;
        }
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> SUBMITTING...';
        submitBtn.disabled = true;
        try {
          await API.post(`/api/cases/${caseData.case_id}/feedback`, {
            analyst_decision: decision,
            notes: notes
          });
          submitBtn.innerHTML = '<i class="fas fa-check"></i> FEEDBACK RECORDED';
          submitBtn.style.background = 'var(--accent-green)';
        } catch (e) {
          submitBtn.innerHTML = '<i class="fas fa-exclamation-circle"></i> ERROR';
          submitBtn.disabled = false;
        }
      });
    }

    // Wire up the Why? button
    const whyBtn = document.getElementById("btn-why-score");
    if (whyBtn) {
      whyBtn.addEventListener("click", async () => {
        const breakdownContainer = document.getElementById("risk-breakdown-container");
        if (breakdownContainer.style.display === "block") {
          breakdownContainer.style.display = "none";
          return;
        }
        
        whyBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> LOADING...';
        whyBtn.disabled = true;
        try {
          const breakdown = await API.get(`/api/cases/${caseData.case_id}/risk-breakdown`);
          
          const factors = breakdown.factors || [];
          const triggeredFactors = factors.filter(f => f.triggered);
          
          breakdownContainer.innerHTML = `
            <h3><i class="fas fa-microscope"></i> Risk Breakdown</h3>
            <p style="font-size: 0.8rem; color: var(--text-muted); margin-bottom: 10px;">Detailed analysis of factors contributing to the final score.</p>
            <table style="width: 100%; border-collapse: collapse; font-size: 0.85rem;">
              <thead>
                <tr style="border-bottom: 1px solid rgba(255,255,255,0.1); color: var(--text-muted); text-align: left;">
                  <th style="padding: 8px;">Factor</th>
                  <th style="padding: 8px;">Points</th>
                  <th style="padding: 8px;">Description</th>
                </tr>
              </thead>
              <tbody>
                ${triggeredFactors.map(f => `
                  <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
                    <td style="padding: 8px; color: var(--accent-red); font-weight: 600;">${escapeHtml(f.name || 'Unknown')}</td>
                    <td style="padding: 8px;">+${f.score || 0}</td>
                    <td style="padding: 8px; color: rgba(255,255,255,0.7);">${escapeHtml(f.description || '')}</td>
                  </tr>
                `).join("")}
              </tbody>
            </table>
          `;
          breakdownContainer.style.display = "block";
        } catch (e) {
          console.error("Failed to load risk breakdown:", e);
          breakdownContainer.innerHTML = `<p style="color: var(--accent-red);"><i class="fas fa-exclamation-triangle"></i> Failed to load risk breakdown.</p>`;
          breakdownContainer.style.display = "block";
        } finally {
          whyBtn.innerHTML = '<i class="fas fa-question-circle"></i> WHY THIS SCORE?';
          whyBtn.disabled = false;
        }
      });
    }
  }

  // -----------------------------------------------------------------
  // 11. renderSAR
  // -----------------------------------------------------------------
  function renderSAR(sarText) {
    const container = document.getElementById("sar-draft");
    if (!container) return;

    if (!sarText) {
      container.innerHTML = '<div class="empty-state"><div class="empty-state-icon"><i class="fas fa-file"></i></div><div class="empty-state-text">No SAR required for this case</div></div>';
      return;
    }

    container.innerHTML = `
      <div class="sar-container">
        <div class="sar-watermark">DRAFT</div>
        <button class="sar-copy-btn" id="sar-copy-btn"><i class="fas fa-copy"></i> Copy</button>
        <div class="sar-text">${escapeHtml(sarText)}</div>
        <div class="sar-footer">
          <i class="fas fa-exclamation-triangle"></i> STATUS: DRAFT — Requires human analyst review before submission to FinCEN
        </div>
      </div>`;

    // Copy handler
    const copyBtn = document.getElementById("sar-copy-btn");
    if (copyBtn) {
      copyBtn.addEventListener("click", () => {
        navigator.clipboard.writeText(sarText).then(() => {
          copyBtn.innerHTML = '<i class="fas fa-check"></i> Copied!';
          setTimeout(() => { copyBtn.innerHTML = '<i class="fas fa-copy"></i> Copy'; }, 2000);
        }).catch(() => {
          showToast("Failed to copy to clipboard", "error");
        });
      });
    }
  }

  // -----------------------------------------------------------------
  // 12. loadAlerts
  // -----------------------------------------------------------------
  async function loadAlerts() {
    try {
      const alerts = await API.get("/api/alerts");
      renderAlerts(alerts);

      // Update notification count (pending alerts)
      const pending = alerts.filter(a => a.status === "new").length;
      const badge = document.getElementById("notification-count");
      if (badge) badge.textContent = pending;
    } catch {
      // silent
    }
  }

  function renderAlerts(alerts) {
    const feed = document.getElementById("alert-feed");
    if (!feed) return;

    if (!alerts || alerts.length === 0) {
      feed.innerHTML = '<div class="empty-state"><div class="empty-state-icon"><i class="fas fa-bell-slash"></i></div><div class="empty-state-text">No alerts</div></div>';
      return;
    }

    feed.innerHTML = alerts.map((alert, i) => {
      const sev = alert.severity || "low";
      const entities = (alert.related_entities || []).join(", ");
      return `
        <div class="alert-card" style="animation-delay: ${i * 0.05}s">
          <div class="alert-severity-dot ${sev}"></div>
          <div class="alert-info">
            <div class="alert-title">${escapeHtml(alert.trigger_rule || "Alert")} — ${sev.toUpperCase()}</div>
            <div class="alert-meta">${alert.alert_id} · ${entities} · ${formatTimeAgo(alert.created_at)}</div>
          </div>
          ${alert.status === "new" ? `<button class="btn-investigate" data-alert-id="${alert.alert_id}">Investigate</button>` : `<span class="status-badge ${alert.status}">${alert.status}</span>`}
        </div>`;
    }).join("");

    // Investigate button and card click handlers
    feed.querySelectorAll(".alert-card").forEach((card, i) => {
      const alert = alerts[i];
      card.addEventListener("click", () => showAlertDetails(alert));

      const btn = card.querySelector(".btn-investigate");
      if (btn) {
        btn.addEventListener("click", (e) => {
          e.stopPropagation();
          investigateAlert(alert.alert_id);
        });
      }
    });
  }

  // -----------------------------------------------------------------
  // 13. setupTabs
  // -----------------------------------------------------------------
  function setupTabs() {
    const tabButtons = document.querySelectorAll(".tab[data-tab]");
    tabButtons.forEach((btn) => {
      btn.addEventListener("click", () => {
        activateTab(btn.dataset.tab);
      });
    });
  }

  function activateTab(tabName) {
    // Buttons
    document.querySelectorAll(".tab[data-tab]").forEach((btn) => {
      btn.classList.toggle("active", btn.dataset.tab === tabName);
      btn.setAttribute("aria-selected", btn.dataset.tab === tabName ? "true" : "false");
    });

    // Panels
    document.querySelectorAll(".tab-content").forEach((panel) => {
      panel.classList.toggle("active", panel.id === `tab-${tabName}`);
    });
  }

  // -----------------------------------------------------------------
  // 14b. Alert Details Modal
  // -----------------------------------------------------------------
  let currentAlertId = null;

  function setupAlertModal() {
    const modal = document.getElementById("alert-detail-modal");
    const btnClose = document.getElementById("alert-modal-close");
    const backdrop = document.getElementById("alert-modal-backdrop");
    const btnInvestigate = document.getElementById("btn-investigate-from-modal");

    if (btnClose) btnClose.addEventListener("click", hideAlertModal);
    if (backdrop) backdrop.addEventListener("click", hideAlertModal);
    if (btnInvestigate) {
      btnInvestigate.addEventListener("click", () => {
        if (currentAlertId) {
          hideAlertModal();
          investigateAlert(currentAlertId);
        }
      });
    }

    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && modal && !modal.classList.contains("hidden")) {
        hideAlertModal();
      }
    });
  }

  function showAlertDetails(alert) {
    const modal = document.getElementById("alert-detail-modal");
    const body = document.getElementById("alert-detail-body");
    const btn = document.getElementById("btn-investigate-from-modal");
    
    if (!modal || !body) return;

    currentAlertId = alert.alert_id;

    const entities = (alert.related_entities || []).join(", ") || "None";
    const source = (alert.source || "System").replace(/_/g, " ");

    body.innerHTML = `
      <div class="alert-detail-row">
        <span class="alert-detail-label">Alert ID</span>
        <span class="alert-detail-val">${escapeHtml(alert.alert_id)}</span>
      </div>
      <div class="alert-detail-row">
        <span class="alert-detail-label">Severity & Status</span>
        <span class="alert-detail-val">
          <span class="alert-severity-dot ${alert.severity || "low"}" style="display:inline-block; position:static;"></span>
          ${(alert.severity || "low").toUpperCase()} · <span class="status-badge ${alert.status || "unknown"}">${alert.status || "unknown"}</span>
        </span>
      </div>
      <div class="alert-detail-row">
        <span class="alert-detail-label">Trigger Rule</span>
        <span class="alert-detail-val">${escapeHtml(alert.trigger_rule || "Unknown")}</span>
      </div>
      <div class="alert-detail-row">
        <span class="alert-detail-label">Source</span>
        <span class="alert-detail-val">${escapeHtml(source)}</span>
      </div>
      <div class="alert-detail-row">
        <span class="alert-detail-label">Related Entities</span>
        <span class="alert-detail-val">${escapeHtml(entities)}</span>
      </div>
      <div class="alert-detail-row">
        <span class="alert-detail-label">Created At</span>
        <span class="alert-detail-val">${formatDateTime(alert.created_at)}</span>
      </div>
    `;

    if (btn) {
      btn.style.display = alert.status === "new" ? "block" : "none";
    }

    modal.classList.remove("hidden");
  }

  function hideAlertModal() {
    const modal = document.getElementById("alert-detail-modal");
    if (modal) modal.classList.add("hidden");
    currentAlertId = null;
  }

  // -----------------------------------------------------------------
  // 14. setupCommandCenter (floating chatbot)
  // -----------------------------------------------------------------
  function setupCommandCenter() {
    const btnNewInvestigation = document.getElementById("btn-new-investigation");
    const input = document.getElementById("mission-input");
    const btnExecute = document.getElementById("btn-execute-mission");

    if (btnNewInvestigation) {
      btnNewInvestigation.addEventListener("click", () => {
        // Open the floating chatbot instead of tab
        const panel = document.getElementById('cc-panel');
        const fab = document.getElementById('cc-fab');
        if (panel && !panel.classList.contains('open')) {
          panel.classList.add('open');
          if (fab) fab.classList.add('open');
        }
        if (input) { input.value = ""; setTimeout(() => input.focus(), 300); }
      });
    }

    if (btnExecute) {
      btnExecute.addEventListener("click", () => executeMission());
    }

    if (input) {
      input.addEventListener("keydown", (e) => {
        if (e.key === "Enter") executeMission();
      });
    }
  }
  
  async function loadPriorityActions() {
    const container = document.getElementById("priority-actions-content");
    if (!container) return;
    
    try {
      const actions = await API.get("/api/actions/priority");
      if (!actions || actions.length === 0) {
        container.innerHTML = '<div class="empty-state-text" style="text-align: center; color: rgba(255,255,255,0.3); padding: 20px;">No high priority actions pending.</div>';
        return;
      }
      
      container.innerHTML = actions.map(a => `
        <div class="priority-action-card" onclick="selectCase('${a.case_id}')">
          <div class="action-header">
            <span class="action-case">${a.case_id}</span>
            <span class="action-impact">${a.impact}</span>
          </div>
          <div class="action-desc">${escapeHtml(a.description)}</div>
          <div class="log-timestamp" style="margin-top: 8px;">${formatTimeAgo(a.timestamp)}</div>
        </div>
      `).join('');
    } catch (err) {
      container.innerHTML = '<div class="empty-state-text">Failed to load actions.</div>';
    }
  }
  
  async function loadEmergingThreats() {
    const container = document.getElementById("emerging-threats-content");
    if (!container) return;
    
    try {
      const threats = await API.get("/api/threat-intel/emerging");
      if (!threats || threats.length === 0) {
        container.innerHTML = '<div class="empty-state-text" style="text-align: center; color: rgba(255,255,255,0.3); padding: 20px;">Monitoring network... No emerging campaigns detected.</div>';
        return;
      }
      
      container.innerHTML = threats.map(t => `
        <div class="threat-card">
          <div class="threat-name"><i class="fas fa-radiation"></i> ${escapeHtml(t.campaign_name)}</div>
          <div class="threat-desc">${escapeHtml(t.description)}</div>
          <div class="threat-stats">
            <span>Confidence: ${t.confidence}%</span>
            <span>Related Cases: ${t.related_cases}</span>
          </div>
        </div>
      `).join('');
    } catch (err) {
      container.innerHTML = '<div class="empty-state-text">Failed to load intel.</div>';
    }
  }
  
  let missionEventSource = null;
  
  async function executeMission() {
    const input = document.getElementById("mission-input");
    const log = document.getElementById("mission-log");
    const btnExecute = document.getElementById("btn-execute-mission");
    
    const command = input ? input.value.trim() : "";
    if (!command) {
      showToast("Please enter a mission objective", "warning");
      return;
    }
    
    if (btnExecute) btnExecute.disabled = true;
    if (input) {
      input.disabled = true;
      input.value = "";
    }
    
    // Append user input to log instead of clearing it
    if (log) {
      // Remove welcome screen if present
      const welcome = log.querySelector('.cc-welcome');
      if (welcome) welcome.remove();

      log.innerHTML += `
        <div class="log-entry info" data-sender="user">
          <span class="log-timestamp">${new Date().toLocaleTimeString('en-US', { hour12: false })}</span>
          <span class="log-agent">YOU</span>
          <span class="log-message" style="color: #eee">"${escapeHtml(command)}"</span>
        </div>
        <div class="log-entry active">
          <span class="log-timestamp">${new Date().toLocaleTimeString('en-US', { hour12: false })}</span>
          <span class="log-agent">CHIEF</span>
          <span class="log-message">Processing mission...</span>
        </div>
      `;
      log.scrollTop = log.scrollHeight;
    }
    
    // Reset agent status bar (in the floating chatbot)
    document.querySelectorAll(".cc-agents-bar .agent-status").forEach(el => {
      el.classList.remove("active", "complete");
    });
    
    // Stop any existing stream
    if (missionEventSource) {
      missionEventSource.close();
    }

    const missionId = "MIS-" + Date.now();
    const missionLogData = [];
    missionLogData.push({
      timestamp: new Date().toISOString(),
      agent: "CHIEF",
      status: "info",
      message: `Initiating mission: "${command}"`
    });
    
    try {
      // POST the mission request, it should return an SSE stream.
      // Fetch API doesn't support SSE well directly without ReadableStream processing,
      // so we use standard fetch for POST, then we actually just do the POST request.
      // Wait, the python implementation returns StreamingResponse on POST.
      // EventSource only supports GET. Let's use fetch and ReadableStream.
      
      const response = await fetch(BASE_URL + "/api/mission", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-API-Key": "fi-hackathon-2026-secret"
        },
        body: JSON.stringify({ command: command })
      });
      
      if (!response.ok) {
        throw new Error(`Mission failed: ${response.status}`);
      }
      
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        
        // Parse SSE lines
        const lines = buffer.split('\n\n');
        buffer = lines.pop(); // keep incomplete part
        
        for (const block of lines) {
          if (block.startsWith('data: ')) {
            const dataStr = block.substring(6);
            try {
              const event = JSON.parse(dataStr);
              missionLogData.push(event);
              handleMissionEvent(event);
            } catch (e) {
              console.error("Failed to parse mission event", dataStr, e);
            }
          }
        }
      }
      
      // Complete
      let hasError = missionLogData.some(ev => ev.status === "error");
      if (log) {
        const d = new Date().toLocaleTimeString('en-US', { hour12: false });
        if (hasError) {
          log.innerHTML += `
            <div class="log-entry" style="border-left-color: var(--accent-red)">
              <span class="log-timestamp">${d}</span>
              <span class="log-agent">CHIEF</span>
              <span class="log-message" style="color: var(--accent-red)">Mission aborted due to errors.</span>
            </div>
          `;
        } else {
          log.innerHTML += `
            <div class="log-entry success">
              <span class="log-timestamp">${d}</span>
              <span class="log-agent">CHIEF</span>
              <span class="log-message">Mission complete. Systems standing by.</span>
            </div>
          `;
        }
        log.scrollTop = log.scrollHeight;
      }
      
      missionLogData.push({
        timestamp: new Date().toISOString(),
        agent: "CHIEF",
        status: hasError ? "error" : "complete",
        message: hasError ? "Mission aborted due to errors." : "Mission complete. Systems standing by."
      });
      
      saveMissionHistory({ id: missionId, command: command, logs: missionLogData, timestamp: new Date().toISOString() });
      renderMissionHistory();
      
      // Update data
      loadCases();
      loadAlerts();
      loadStats();
      loadPriorityActions();
      loadEmergingThreats();
      
    } catch (err) {
      console.error(err);
      if (log) {
        const d = new Date().toLocaleTimeString('en-US', { hour12: false });
        log.innerHTML += `
          <div class="log-entry" style="border-left-color: var(--accent-red)">
            <span class="log-timestamp">${d}</span>
            <span class="log-agent">SYSTEM</span>
            <span class="log-message" style="color: var(--accent-red)">Error: ${escapeHtml(err.message)}</span>
          </div>
        `;
        log.scrollTop = log.scrollHeight;
      }
      
      missionLogData.push({
        timestamp: new Date().toISOString(),
        agent: "SYSTEM",
        status: "error",
        message: `Error: ${err.message}`
      });
      saveMissionHistory({ id: missionId, command: command, logs: missionLogData, timestamp: new Date().toISOString() });
      renderMissionHistory();
      
      showToast(`Mission failed: ${err.message}`, "error");
    } finally {
      if (btnExecute) btnExecute.disabled = false;
      if (input) {
        input.disabled = false;
        input.focus();
      }
    }
  }
  
  function handleMissionEvent(event) {
    const log = document.getElementById("mission-log");
    if (!log) return;
    
    // format time
    const time = event.timestamp ? new Date(event.timestamp).toLocaleTimeString('en-US', { hour12: false }) : new Date().toLocaleTimeString('en-US', { hour12: false });
    
    // Determine CSS class based on status
    let statusClass = "info";
    if (event.status === "in_progress") statusClass = "active";
    if (event.status === "complete") statusClass = "success";
    if (event.status === "error") statusClass = ""; // red is default if not set, but let's just let it be
    
    let resultHtml = "";
    if (event.result && Object.keys(event.result).length > 0) {
        // If there's a case_id, make it clickable
        if (event.result.case_id) {
             resultHtml = `<div class="log-result" style="cursor: pointer" onclick="selectCase('${event.result.case_id}')"><i class="fas fa-folder-open"></i> Generated Case: ${event.result.case_id} (Click to view)</div>`;
        } else {
             resultHtml = `<div class="log-result">${escapeHtml(JSON.stringify(event.result, null, 2))}</div>`;
        }
    }
    
    log.innerHTML += `
      <div class="log-entry ${statusClass}">
        <span class="log-timestamp">${time}</span>
        <span class="log-agent">${escapeHtml(event.agent.toUpperCase())}</span>
        <div class="log-message">
          ${escapeHtml(event.message)}
          ${resultHtml}
        </div>
      </div>
    `;
    
    log.scrollTop = log.scrollHeight;
    
    // Update Agent Status Bar (in the floating chatbot)
    if (event.agent !== "orchestrator" && event.agent !== "system") {
      // Find the corresponding pill in the chatbot's agent bar
      const pills = document.querySelectorAll(".cc-agents-bar .agent-status");
      let targetPill = null;
      pills.forEach(p => {
        if (event.agent.toLowerCase().includes(p.dataset.agent)) {
          targetPill = p;
        }
      });
      
      if (targetPill) {
        if (event.status === "in_progress") {
          targetPill.classList.add("active");
          targetPill.classList.remove("complete");
        } else if (event.status === "complete") {
          targetPill.classList.remove("active");
          targetPill.classList.add("complete");
        }
      }
    }
  }

  function saveMissionHistory(mission) {
    let history = [];
    try {
      history = JSON.parse(localStorage.getItem('fi_mission_history') || '[]');
    } catch(e) {}
    history.unshift(mission); // add to top
    if (history.length > 50) history.pop(); // keep last 50
    localStorage.setItem('fi_mission_history', JSON.stringify(history));
  }

  function renderMissionHistory() {
    const list = document.getElementById("mission-history-list");
    if (!list) return;
    
    let history = [];
    try {
      history = JSON.parse(localStorage.getItem('fi_mission_history') || '[]');
    } catch(e) {}
    
    if (history.length === 0) {
      list.innerHTML = '<div style="color: var(--text-muted);"><i class="fas fa-info-circle"></i> No historical missions found. Execute a mission in the Command Center to record history.</div>';
      return;
    }
    
    list.innerHTML = history.map(mission => {
      const d = new Date(mission.timestamp).toLocaleString();
      let isError = mission.logs[mission.logs.length-1].status === "error";
      let statusColor = isError ? "var(--accent-red)" : "#00ffaa";
      
      return `
        <div style="background: rgba(0,0,0,0.4); border: 1px solid rgba(255,255,255,0.1); border-left: 3px solid ${statusColor}; padding: 12px; border-radius: 4px;">
          <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
            <strong style="color: #fff; font-size: 0.85rem;">Mission: ${escapeHtml(mission.command)}</strong>
            <span style="color: var(--text-muted); font-size: 0.75rem;">${d}</span>
          </div>
          <div style="max-height: 200px; overflow-y: auto; background: #050101; padding: 10px; font-size: 0.75rem; border: 1px solid rgba(255,255,255,0.05); border-radius: 4px;">
            ${mission.logs.map(log => {
              let statusClass = "info";
              if (log.status === "in_progress") statusClass = "active";
              if (log.status === "complete" || log.status === "success") statusClass = "success";
              if (log.status === "error") statusClass = "";
              
              let resultHtml = "";
              if (log.result && Object.keys(log.result).length > 0) {
                  resultHtml = `<div class="log-result">${escapeHtml(JSON.stringify(log.result, null, 2))}</div>`;
              }
              
              return `
                <div class="log-entry ${statusClass}">
                  <span class="log-timestamp">${new Date(log.timestamp).toLocaleTimeString('en-US', { hour12: false })}</span>
                  <span class="log-agent" style="min-width: 120px;">${escapeHtml(log.agent.toUpperCase())}</span>
                  <div class="log-message">
                    ${escapeHtml(log.message)}
                    ${resultHtml}
                  </div>
                </div>
              `;
            }).join('')}
          </div>
        </div>
      `;
    }).join('');
  }


  // -----------------------------------------------------------------
  // 16. investigateAlert
  // -----------------------------------------------------------------
  async function investigateAlert(alertId) {
    showToast(`Investigating alert ${alertId}...`, "info");

    try {
      const result = await API.post(`/api/alerts/${alertId}/investigate`, {});

      showToast(`Alert investigated! Case: ${result.case_id} (Score: ${result.fraud_score})`, "success");

      await loadCases();
      await loadAlerts();
      await loadStats();
      selectCase(result.case_id);

    } catch (err) {
      showToast(`Alert investigation failed: ${err.message}`, "error");
    }
  }

  // -----------------------------------------------------------------
  // 17. showToast
  // -----------------------------------------------------------------
  function showToast(message, type = "info") {
    const container = document.getElementById("toast-container");
    if (!container) return;

    const toast = document.createElement("div");
    toast.className = `toast ${type}`;
    toast.innerHTML = `
      <span class="toast-message">${escapeHtml(message)}</span>
      <button class="toast-close" aria-label="Dismiss">&times;</button>
    `;

    container.appendChild(toast);

    // Close button
    const closeBtn = toast.querySelector(".toast-close");
    if (closeBtn) {
      closeBtn.addEventListener("click", () => dismissToast(toast));
    }

    // Auto-dismiss after 4 seconds
    setTimeout(() => dismissToast(toast), 4000);
  }

  function dismissToast(toast) {
    if (!toast || !toast.parentNode) return;
    toast.classList.add("dismissing");
    setTimeout(() => {
      if (toast.parentNode) toast.parentNode.removeChild(toast);
    }, 300);
  }

  // -----------------------------------------------------------------
  // 18. Utilities
  // -----------------------------------------------------------------

  function formatTimeAgo(dateStr) {
    if (!dateStr) return "";
    try {
      const date = new Date(dateStr);
      const now = new Date();
      const diffMs = now - date;
      const diffSec = Math.floor(diffMs / 1000);
      const diffMin = Math.floor(diffSec / 60);
      const diffHr = Math.floor(diffMin / 60);
      const diffDay = Math.floor(diffHr / 24);

      if (diffSec < 60) return "just now";
      if (diffMin < 60) return `${diffMin}m ago`;
      if (diffHr < 24) return `${diffHr}h ago`;
      if (diffDay < 30) return `${diffDay}d ago`;
      return date.toLocaleDateString();
    } catch {
      return dateStr;
    }
  }

  function formatStatus(status) {
    if (!status) return "";
    return status.split("_").map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase()).join(" ");
  }

  function formatDateTime(dateStr) {
    if (!dateStr) return "";
    try {
      const d = new Date(dateStr);
      return d.toLocaleString("en-US", {
        month: "short", day: "numeric",
        hour: "2-digit", minute: "2-digit",
        hour12: false,
      });
    } catch {
      return dateStr;
    }
  }

  function getRiskColor(classification) {
    const c = (classification || "").toLowerCase();
    if (c.includes("critical") || c.includes("high")) return "#ff1a1a";
    if (c.includes("medium")) return "#ff9999";
    return "#ffffff";
  }

  function getRiskColorVar(classification) {
    const c = (classification || "").toLowerCase();
    if (c.includes("critical") || c.includes("high")) return "var(--accent-red)";
    if (c.includes("medium")) return "#ff9999";
    return "#ffffff";
  }

  function getRiskClass(classification) {
    const c = (classification || "").toLowerCase();
    if (c.includes("critical") || c.includes("high")) return "risk-high";
    if (c.includes("medium")) return "risk-medium";
    return "risk-low";
  }

  function getRiskPillClass(classification) {
    return getRiskClass(classification);
  }

  function escapeHtml(str) {
    if (!str) return "";
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  }

  function truncate(str, len) {
    if (!str) return "";
    return str.length > len ? str.slice(0, len) + "…" : str;
  }

  function setPlaceholder(elementId, text) {
    const el = document.getElementById(elementId);
    if (el) el.innerHTML = `<div class="empty-state"><div class="empty-state-text">${escapeHtml(text)}</div></div>`;
  }

  function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  // -----------------------------------------------------------------
  // 19. Ticker Time
  // -----------------------------------------------------------------
  function updateTickerTime() {
    const el = document.getElementById("ticker-time");
    if (el) {
      const now = new Date();
      el.textContent = now.toLocaleTimeString('en-US', { hour12: false }) + " UTC";
    }
  }

  // -----------------------------------------------------------------
  // Bootstrap
  // -----------------------------------------------------------------
  document.addEventListener("DOMContentLoaded", () => {
    initDashboard();
    setupTabs();
    setupCommandCenter();
    setupAlertModal();

    const searchInput = document.getElementById("search-input");
    const searchBtn = document.getElementById("search-btn");
    
    if (searchInput) {
      searchInput.addEventListener("input", filterAndRenderCases);
      searchInput.addEventListener("keyup", (e) => {
        if (e.key === "Enter") filterAndRenderCases();
      });
    }
    
    if (searchBtn) {
      searchBtn.addEventListener("click", filterAndRenderCases);
    }

    // System Health Check Polling
    async function updateSystemHealth() {
      try {
        const health = await API.get("/api/health");
        const ticker = document.getElementById("system-ticker");
        if (ticker && health) {
          const dbColor = health.mongodb_connected ? "green" : "var(--accent-red)";
          const statusColor = health.status === "ok" ? "green" : "var(--accent-red)";
          ticker.innerHTML = `
            <div class="ticker-item"><span class="ticker-dot ${dbColor}"></span> MONGODB ATLAS: ${health.mongodb_connected ? 'CONNECTED' : 'OFFLINE'}</div>
            <div class="ticker-item"><span class="ticker-dot ${statusColor}"></span> SYSTEM: ${health.status.toUpperCase()}</div>
            <div class="ticker-item"><span class="ticker-dot green"></span> VERSION: ${health.version}</div>
            <div class="ticker-item">|</div>
            <div class="ticker-item"><i class="fas fa-shield-alt" style="color: var(--accent-red); font-size: 0.6rem;"></i> THREAT LEVEL: ELEVATED</div>
            <div class="ticker-item">|</div>
            <div class="ticker-item" id="ticker-time"></div>
          `;
          // Time element was overwritten, restart time update
          updateTickerTime();
        }
      } catch (e) {
        console.error("Health check failed", e);
      }
    }
    
    // Update time initially and setup polling for health
    updateSystemHealth();
    setInterval(updateSystemHealth, 30000);
    setInterval(updateTickerTime, 1000);

  });

})();
