---
name: fullstack-ai-agent-development-guidelines
description: Generic full-stack coding guidelines for building fast, resilient MVP/POC applications using React, Vite, Tailwind CSS, FastAPI, SQL, LangChain, LangGraph, and CrewAI.
---

# Full-Stack AI Application Development Guidelines

A set of generic coding standards and development principles for building maintainable, resilient, and production-ready POC/MVP applications.

---

## 1. Directory & Code Organization

* **Flat File Structure:** Do not create nested subfolders within your project directories. Keep the code organized by separating distinct concerns across individual files placed in the same folder.
* **Separation of Concerns:** Keep client-side presentation code in the frontend directory and server-side/agent logic in the backend directory.
* **Modularity:** Each file should own a single, clear responsibility rather than combining unrelated concerns into monolithic scripts.

---

## 2. Frontend Guidelines (React + Vite + Tailwind CSS)

* **Design Specification Adherence:** Strictly follow `DESIGN.md` for all styling rules, color palettes, spacing tokens, typography, and component specifications.
* **Dual Button Paradigm:**
  * Marketing and primary conversion actions use fully rounded pill shapes.
  * Application controls, navigation items, and chrome actions use tight square corners with subtle rounding.
* **Surfaces & Elevation:**
  * Define surfaces using subtle 1px hairline borders rather than heavy drop shadows.
  * Use low-alpha, layered micro-shadows only when an element needs to float over the canvas.
* **Component Design:**
  * Keep components self-contained, props-driven, and functional.
  * Avoid unnecessary abstraction layers, wrapper divs, or custom CSS when utility classes suffice.

---

## 3. Backend Guidelines (FastAPI + SQL)

* **Clean, Pragmatic Coding Style:**
  * Write clear, readable, and direct code.
  * Avoid overengineering: do not introduce complex class hierarchies, abstract base classes, or chains of private helper functions that obscure execution flow and require constant context switching.
  * Prefer straightforward functions with descriptive names, type annotations, and explicit return types.
* **Leverage Existing Libraries:**
  * Do not reinvent wheels. Use standard, battle-tested open-source libraries for schema validation, HTTP communication, database handling, and error recovery.
* **Resilience & Retries with Tenacity:**
  * Always wrap network calls, external service requests, database transactions, and LLM queries with retry decorators from `tenacity`.
  * Configure exponential backoff and explicit retry limits to handle transient failures gracefully.
* **Structured Centralized Logging:**
  * Use Python's built-in `logging` module throughout the codebase.
  * Avoid bare `print()` statements.
  * Ensure all operations, tool executions, state transitions, and error states are clearly logged with timestamps and contextual log levels.
* **Database & Data Access:**
  * Use standard SQL drivers (`psycopg2-binary` or lightweight local equivalents).
  * Keep data access routines explicit, parameterized, and easy to inspect.
* **Algorithmic & Loop Efficiency:**
  * Never write inefficient, unoptimized nested loops (e.g., $O(N^2)$ iterations or repeated in-memory linear scans for keyed lookups).
  * Use indexed structures (dictionaries, hash sets) for instant lookups instead of scanning collections repeatedly.
  * Proactively profile, identify, and refactor any inefficient procedural iterations or blocking busy-waits.
* **SQL Query Optimization & Hygiene:**
  * Never write unoptimized, unindexed, or unconstrained SQL queries.
  * Avoid unneeded `SELECT *` across broad tables; specify exact projected columns and apply `LIMIT` clauses where appropriate.
  * Eliminate N+1 query patterns by fetching required relationships in batched queries or joins.
  * Audit all queries to ensure they use parameterized inputs and proper indexing.

---

## 4. Autonomous Agent Architecture (LangChain, LangGraph & CrewAI)

* **Pluggable LLM Provider:**
  * Keep model initialization isolated and configurable via environment variables.
  * Support fast, low-latency testing using high-throughput providers (such as Groq) during early prototyping, while maintaining easy switching to other model APIs.
* **Agent Framework Roles:**
  * **LangChain:** Prompts, structured output parsers, and tool interfaces.
  * **LangGraph:** Stateful and cyclical decision flows where transitions and states are explicitly defined.
  * **CrewAI:** Multi-agent role division when distinct autonomous personas collaborate toward a shared goal.
* **Tool Safety & Idempotency:**
  * Every agent tool must define strict type hints, input models, and clear documentation.
  * Mutation actions must be idempotent to ensure safe retries in case of transient execution timeouts.
  * Implement safe execution thresholds: when confidence is low or action parameters exceed predefined limits, gracefully divert to human review.

---

## 5. Development Principles for MVP / POC

* **Avoid Premature Optimization:** Focus on delivering a solid, end-to-end working flow first.
* **Simplicity Over Abstraction:** Write code that is easy to read, debug, and modify.
* **Fail Fast & Surface Errors:** Catch exceptions early, log the complete trace, and return actionable, clear error responses.

---

## 6. Verification, Testing & Zero-Error Quality Standards

* **Phase-by-Phase Testing:**
  * Test every feature, schema, and API endpoint thoroughly during its respective phase before proceeding to the next.
  * Never advance with known bugs, unhandled exceptions, or failing dependencies. Any flaw discovered during verification must be resolved and re-verified immediately.
* **Backend Compilation & Diagnostic Integrity:**
  * Validate Python syntax and import hygiene across the backend using `python -m compileall <backend_directory>`.
  * Maintain comprehensive, automated test scripts covering database connections, tool execution, safety boundaries, and end-to-end agent workflows.
* **Frontend Production Build Verification:**
  * Always verify the frontend by running `npm run build` in the frontend directory to guarantee zero JSX syntax errors, no missing package imports, and complete CSS/Vite bundling compliance.
* **Zero-Error Handover Guarantee:**
  * Verify the full application lifecycle end-to-end so that the user is never trapped in runtime errors, broken configurations, or missing package dependencies upon launching the application.

---

## 7. Fit-to-Screen Viewport Architecture (Zero-Window-Scroll Standard)

* **Viewport Enclosure:**
  * Design web application dashboards to fit the user's viewport screen (`h-screen overflow-hidden`) without requiring vertical window scrollbars on standard desktop and laptop displays.
  * Use CSS flexbox with `flex-1 min-h-0` for all internal children so content flexibly expands or contracts within available pixel height.
* **Internal Scrollers Only:**
  * Scrolling should only happen within specific, designated content panels (e.g., chat message list, terminal trace, or ledger table) via `overflow-y-auto`, leaving the navigation bar, status headers, and layout structure fixed in place.
* **Compact Status Headers:**
  * Keep banners and ribbons compact (~32px to 48px) rather than bulky hero sections so that maximal vertical real estate is reserved for the operational workspace.

---

## 8. Multilingual Agent Support (Separation of Core Ops & Regional Localization)

* **Separation of Concerns:**
  * Keep internal agent orchestration, tool execution, telemetry diagnoses, database queries, and terminal logs strictly in standard English for deterministic execution, auditing, and observability.
  * Localize merchant-facing prompt suggestions, conversational greetings, and final resolution messages into regional native languages (e.g., top 10 Indian languages: English, Hindi, Marathi, Gujarati, Bengali, Tamil, Telugu, Kannada, Malayalam, Punjabi).
* **Deterministic Database-First Diagnosis:**
  * Anomaly detection and scenario branching must be driven primarily by structured database flags and ledger telemetry rather than fragile keyword matching on localized user input.
* **Native Regional Templates:**
  * Maintain natural, accurate native-script message templates with parameter interpolation for all supported scenarios.

