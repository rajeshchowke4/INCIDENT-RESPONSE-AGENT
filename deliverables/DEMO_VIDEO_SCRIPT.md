# ResqOps Demo Video Scripts

This document provides two ready-to-record video scripts for your hackathon submission:
1. **Option A: The 60-Second Rapid Demo Hook** (High-energy, direct, perfect for judging rounds & social video)
2. **Option B: The 3-Minute Comprehensive Technical Walkthrough** (Detailed architecture, code, and live learning demo)

---

## Option A: 60-Second Rapid Demo Video Script

| Time | Visual / Screen Action | Voiceover Narration |
| :--- | :--- | :--- |
| **0:00 - 0:10** | Show ResqOps Dashboard. Red glowing alert: `KafkaBrokerJVMHeapCriticallyHigh` with raw stack trace. | *"It's 3 AM. A Kafka broker is crashing with an OutOfMemoryError. If you ask a standard AI chatbot, it tells you: 'Just restart the broker'. That reboot would cause a catastrophic partition rebalance that takes down your entire cluster."* |
| **0:10 - 0:25** | Click **"⚡ 1. Kafka OOM Heap"** scenario, then click **"Trigger Dual-Agent Investigation"**. Split screen appears. | *"This is ResqOps, an SRE Incident Copilot built on Vectorize Hindsight. On the left, watch the stateless LLM struggle with 35% confidence and generic advice that could worsen the outage. On the right, Hindsight kicks in."* |
| **0:25 - 0:40** | Zoom in on right box showing Hindsight recall badge `INC-2024-1014` and bold warning against rebooting. | *"Hindsight instantly recalls Incident #INC-2024-1014 from October. It diagnoses the exact root cause: uncompressed 64MB batches flooding payment-events. It warns you NOT to reboot, and hands you the exact CLI command to throttle the topic in 90 seconds."* |
| **0:40 - 0:55** | Click **"✨ 5. Novel RabbitMQ Outage"**, click **"Retain in Hindsight"**, then re-trigger alert to show instant 99.4% confidence. | *"And ResqOps learns continuously. When a brand new RabbitMQ outage hits, the engineer inputs the fix. ResqOps synthesizes a blameless post-mortem and retains it in Hindsight. Next time that error strikes, the agent immediately knows how to fix it."* |
| **0:55 - 1:00** | Full dashboard view with Hindsight Memory Bank counter incremented. | *"Persistent institutional memory that turns 60-minute downtime into a 90-second fix. That is ResqOps with Vectorize Hindsight."* |

---

## Option B: 3-Minute Comprehensive Walkthrough Script

### Act 1: The Problem & The Amnesia of Modern AI (0:00 - 0:45)
* **Screen:** Open terminal or slide showing: *"Why AI Chatbots Fail at 3 AM"*.
* **Voiceover:**
  > *"Every engineering organization suffers from institutional amnesia. When a critical database locks up or a Kubernetes pod goes into CrashLoopBackOff, Mean Time To Resolution depends on whether the on-call engineer remembers a previous post-mortem from 6 months ago. 
  > If you ask standard AI models like ChatGPT or Claude, they give generic textbook advice. Worse, they often recommend actions like restarting an active broker that can trigger catastrophic cascading failures.
  > Today, we introduce ResqOps: an autonomous SRE Incident Response Copilot powered by Vectorize Hindsight."*

### Act 2: Architecture & Memory Integration (0:45 - 1:30)
* **Screen:** Switch to code editor showing `backend/memory/hindsight_manager.py` and `deliverables/HINDSIGHT_ARCHITECTURE.md`.
* **Voiceover:**
  > *"ResqOps leverages Vectorize Hindsight's Python client with three core operations:
  > First, our memory bank `sre-production-incidents` catalogs structured post-mortems including verified mitigations and anti-patterns to avoid.
  > Second, when an alert fires from Prometheus or PagerDuty, ResqOps executes multi-strategy recall across semantic, keyword, and telemetry signatures.
  > Third, for fast inference, we route queries through Groq Cloud utilizing Llama 3.3 70B for sub-second responses."*

### Act 3: Live Dual-Agent Demonstration (1:30 - 2:30)
* **Screen:** Open browser at `http://localhost:8000`.
* **Action 1:** Click **"🔥 2. Postgres Deadlock (503)"**. Show error: `Process 19283 waits for ExclusiveLock on relation 'billing_ledger'`.
* **Action 2:** Click **"Trigger Dual-Agent Investigation"**.
* **Voiceover:**
  > *"Let's test Scenario 2: Postgres connection pool exhaustion. 
  > Notice the stark contrast on screen. 
  > On the left, the stateless agent suggests scaling up the database or restarting PgBouncer—actions that would cause a thunder herd connection storm.
  > On the right, ResqOps identifies the exact match from our institutional memory: Incident #INC-2024-1102. It explains that the affiliate payout cron was taking exclusive table locks, provides the specific SQL query to kill the blocking PID, and shows the emergency Celery queue pause command. Estimated MTTR drops from 45 minutes to 90 seconds."*

### Act 4: The Live Learning Cycle (2:30 - 3:00)
* **Screen:** Click **"✨ 5. Novel RabbitMQ Outage"**.
* **Action:**
  1. Trigger investigation -> show: `NOVEL - Learn via Retain Tab`.
  2. Switch to the **"Retain Post-Mortem"** tab.
  3. Click **"Synthesize Post-Mortem & Retain in Hindsight"**.
  4. Notification appears confirming memory retention into Hindsight.
  5. Click **"Trigger Dual-Agent Investigation"** again on the same alert.
* **Voiceover:**
  > *"Now watch ResqOps learn in real-time. We introduce a novel RabbitMQ dead-letter queue outage that has never occurred in our company's history. 
  > ResqOps investigates and correctly identifies zero memory matches.
  > Once our team resolves the incident by adding Jackson ObjectMapper properties, we click 'Synthesize Post-Mortem & Retain in Hindsight'.
  > The blameless post-mortem is automatically cataloged in the memory bank. 
  > When we re-trigger the investigation on that exact same telemetry, ResqOps instantly recognizes the incident with 99.4% confidence and delivers the proven runbook.
  > This is how AI agents evolve from static chatbots into institutional knowledge partners. Thank you."*
