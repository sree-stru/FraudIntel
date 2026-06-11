# FraudIntel — Demo Video Script (3 Minutes)

> **Format:** Hackathon submission video
> **Length:** 3:00
> **Resolution:** 1080p minimum
> **Tone:** Confident, authoritative, fast-paced

---

## 0:00 – 0:30 | THE HOOK

| Time | Visual | Narration |
|------|--------|-----------|
| 0:00 | **Black screen** → Bold white text fades in: **"$4.4 TRILLION lost to financial crime annually"** | *(silence — let the number land for 2 seconds)* |
| 0:04 | Text dissolves. New stat: **"95% of fraud alerts are false positives"** | "Every year, four point four *trillion* dollars disappears to financial crime. Legacy systems generate millions of alerts — but up to ninety-five percent are false positives." |
| 0:14 | **Cut to:** FraudIntel dashboard — dark mode, cases loaded in sidebar, stat cards showing live numbers, alert feed scrolling | "Investigators are drowning in noise." |
| 0:18 | Camera slowly zooms into the dashboard. Logo pulses. | "Meet **FraudIntel** — an AI investigation agent that doesn't just *detect* fraud." |
| 0:25 | Quick montage: network graph animating, risk score gauge filling, SAR text appearing | "It *investigates* it." |

> **🎬 Director's Note:** Use a dramatic bass drop or impact sound at 0:25 when "investigates" lands.

---

## 0:30 – 1:30 | THE LIVE INVESTIGATION

| Time | Visual | Narration |
|------|--------|-----------|
| 0:30 | Mouse clicks **"+ New Investigation"** button. Modal slides up. | "Watch what happens when we investigate a suspicious account." |
| 0:35 | Type **ACC-001** into the input field. Click **"Start Investigation"**. | "We enter an account ID — and FraudIntel's multi-agent system activates." |
| 0:40 | Progress area appears: `⏳ Collecting evidence...` → `🔍 Running risk analysis...` | "Five specialized AI agents work together — an Evidence Gatherer pulls transaction records and entity networks..." |
| 0:50 | Progress continues. Brief pause for effect. | "...a Risk Scorer evaluates thirteen fraud indicators... an Auditor challenges the findings for bias..." |
| 1:00 | Progress: `✅ Investigation complete!` Toast notification slides in: *"Investigation complete! Case: INV-2026-XXXX (Score: 78)"* | "...a Compliance Agent checks regulatory requirements... and a Report Generator compiles everything into a structured case file." |
| 1:05 | Modal closes. New case appears at top of sidebar — **score badge 78, HIGH RISK** in amber. Click the case. | "In just ninety seconds, FraudIntel has completed what would take a human analyst four to six hours." |
| 1:12 | **Network Graph tab** activates. D3.js force graph animates into view — nodes spread out, edges connect, red glow on flagged nodes. | "The network graph reveals a hidden fraud ring — four accounts sharing the same device fingerprint and VPN IP address." |
| 1:22 | Hover over the central device node. Tooltip appears showing connections. Highlight the red-glowing nodes. | "This is a classic bust-out scheme. The AI identified it by traversing entity relationships across three degrees of separation." |

> **🎬 Director's Note:** Let the network graph animate for at least 5 seconds. The visual is stunning and demonstrates real-time analysis.

---

## 1:30 – 2:15 | THE FEATURES

| Time | Visual | Narration |
|------|--------|-----------|
| 1:30 | Click **Timeline** tab. Vertical timeline renders with colored dots and staggered animation. | "FraudIntel reconstructs the complete investigation timeline — from the first suspicious transaction to the alert trigger, highlighting critical moments." |
| 1:38 | Scroll through timeline entries. Pause on a critical-severity entry (red pulsing dot). | "Each event is severity-coded — so analysts can immediately focus on what matters." |
| 1:44 | Click **Report** tab. Score banner appears: **78/100 HIGH RISK**. Gauge bar fills with amber. | "The investigation report provides full transparency." |
| 1:50 | Scroll through report sections: Executive Summary → Key Findings (bulleted) → Fraud Indicators | "Evidence collected. Risk score breakdown. Key findings. Every conclusion is traced back to specific evidence." |
| 1:58 | Pause on the **Recommended Actions** section. | "And clear recommended actions — escalate, freeze, file a report." |
| 2:02 | Click **SAR Draft** tab. SAR text appears with **DRAFT** watermark. | "For high-risk cases, FraudIntel automatically generates a FinCEN-compliant Suspicious Activity Report draft..." |
| 2:08 | Click the **📋 Copy** button → shows "✅ Copied!" | "...saving compliance teams hours of manual documentation. One click to copy, review, and file." |

> **🎬 Director's Note:** Move through tabs at a steady pace. Don't rush — each tab is a "wow moment."

---

## 2:15 – 2:45 | THE ARCHITECTURE

| Time | Visual | Narration |
|------|--------|-----------|
| 2:15 | **Cut to:** Architecture diagram overlay (dark background, neon-accented flow diagram) | "Under the hood, FraudIntel is built on **Google Cloud** with the **Agent Development Kit**." |
| 2:20 | Highlight: **Gemini 3 Flash** box glows | "**Gemini 3** serves as the reasoning engine — orchestrating five specialized agents through a sequential pipeline." |
| 2:26 | Highlight: **MongoDB Atlas + MCP** box glows | "The **MongoDB Atlas MCP server** provides standardized database access — enabling graph traversal for fraud ring detection..." |
| 2:32 | Highlight: connections between components | "...vector search for pattern matching, and real-time aggregation pipelines for risk scoring." |
| 2:38 | Zoom out to show full architecture: `User → FastAPI → ADK Orchestrator → [5 Agents] → MongoDB via MCP` | "All wrapped in a production-ready FastAPI backend with a real-time dashboard." |

> **🎬 Director's Note:** The architecture slide should be pre-designed. Keep it clean — no more than 8 boxes. Use the same color palette as the dashboard (dark navy + blue/amber/red accents).

---

## 2:45 – 3:00 | THE CLOSE

| Time | Visual | Narration |
|------|--------|-----------|
| 2:45 | **Cut back to:** Dashboard with multiple cases visible, alerts streaming, stats populated | "FraudIntel transforms fraud investigation from a manual, error-prone process..." |
| 2:50 | Slow zoom out. Dashboard fades slightly. | "...into an AI-powered, transparent, and fully auditable system." |
| 2:54 | **Black screen** → FraudIntel logo (🛡️) fades in center | "Because in the fight against financial crime..." |
| 2:57 | Tagline appears below logo: **"You don't just need alerts — you need an investigator."** | "...you don't just need alerts. You need an investigator." |
| 3:00 | Hold logo + tagline for 1 second. Fade to black. | *(end)* |

> **🎬 Director's Note:** End on the tagline. No call-to-action — this is a hackathon, not a sales pitch. Let the product speak.

---

## Production Notes

### Pre-Recording Checklist

- [ ] Run `python -m data.seed_data` to populate MongoDB with demo data
- [ ] Run `python test_setup.py` to verify all systems are green
- [ ] Start the server: `python -m uvicorn api.server:app --port 8080`
- [ ] Open `http://localhost:8080` in a clean browser window
- [ ] Verify dashboard loads with stat cards populated and cases in sidebar
- [ ] Hide bookmarks bar, close all other tabs
- [ ] Set browser zoom to 100% (or 90% if on a smaller screen)
- [ ] Disable all browser notifications and extensions

### Recording Setup

| Setting | Value |
|---------|-------|
| Resolution | 1920×1080 minimum (4K preferred) |
| Frame Rate | 30fps |
| Browser | Chrome (latest, dark mode OS theme) |
| Recording Tool | OBS Studio, ScreenFlow, or Loom |
| Mouse | Smooth, deliberate movements — no jittering |
| Cursor | Default system cursor (no custom cursors) |

### Audio

- Use a **professional microphone** (Blue Yeti, HyperX, or similar)
- Record narration separately if possible (easier to edit)
- Add **subtle background music** — royalty-free, instrumental, low-energy electronic
  - Suggestions: [Artlist](https://artlist.io), [Epidemic Sound](https://epidemicsound.com)
  - Genre: Ambient tech / minimal electronic
  - Volume: -20dB below narration
- Include **captions/subtitles** (auto-generate via YouTube, then review)

### Architecture Diagram Elements

```
┌─────────────────────────────────────────────┐
│              FraudIntel Dashboard            │
│         (HTML / CSS / D3.js / Vanilla JS)    │
└──────────────────┬──────────────────────────┘
                   │ REST API
┌──────────────────▼──────────────────────────┐
│            FastAPI Backend (Python)          │
│       /api/investigate  /api/cases  etc.     │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│       Google ADK Orchestrator (LlmAgent)     │
│              Gemini 3 Flash                  │
├──────────────────────────────────────────────┤
│  SequentialAgent Pipeline:                   │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐  │
│  │ Evidence   │ │   Risk    │ │  Auditor  │  │
│  │ Gatherer   │ │  Scorer   │ │  Agent    │  │
│  └───────────┘ └───────────┘ └───────────┘  │
│  ┌───────────┐ ┌───────────┐                │
│  │Compliance │ │  Report   │                │
│  │  Agent    │ │ Generator │                │
│  └───────────┘ └───────────┘                │
└──────────────────┬──────────────────────────┘
                   │ MCP Protocol
┌──────────────────▼──────────────────────────┐
│         MongoDB Atlas (via MCP Server)       │
│  ┌────────────┐ ┌─────────┐ ┌────────────┐  │
│  │Transactions│ │ Alerts  │ │Entity Graph│  │
│  └────────────┘ └─────────┘ └────────────┘  │
│  ┌────────────┐ ┌─────────┐ ┌────────────┐  │
│  │ Customers  │ │ Cases   │ │  Patterns  │  │
│  └────────────┘ └─────────┘ └────────────┘  │
└──────────────────────────────────────────────┘
```

### Timing Summary

| Section | Duration | Content |
|---------|----------|---------|
| Hook | 30s | Problem statement + first glimpse |
| Live Demo | 60s | Full investigation walkthrough |
| Features | 45s | Timeline, Report, SAR tabs |
| Architecture | 30s | Tech stack overview |
| Close | 15s | Tagline + logo |
| **Total** | **3:00** | |
