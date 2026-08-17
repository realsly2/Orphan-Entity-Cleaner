# Security Policy

## English Version

### Supported Versions

Orphan Cleaner is a small, single-maintainer Home Assistant custom integration. Only the **latest published release** is supported with security fixes. There is no long-term support for older versions — please always update to the newest release via HACS before reporting an issue.

### Scope

Orphan Cleaner is a HACS **custom integration**, not part of Home Assistant Core and not reviewed or vetted by Home Assistant / Nabu Casa. It runs with the same trust level as any other custom integration you install manually. Specifically in scope for this policy:

- The `custom_components/orphan_cleaner/` integration code (services, config flow, API views).
- The sidebar panel (`frontend/orphan-cleaner-panel.js`).

Out of scope: vulnerabilities in Home Assistant Core itself, in HACS, or in third-party dependencies — please report those to the respective projects.

Given what this integration does (it can **permanently delete entities** from your Entity Registry), a security-relevant report is anything that would let it:

- Delete or modify entities without an authenticated admin user explicitly triggering it.
- Bypass the `require_admin` / `requires_auth` checks on the panel or the `/api/orphan_cleaner/*` endpoints.
- Read or write files outside the intended Home Assistant config directory (e.g. via the backup export).
- Execute arbitrary code through the panel or a service call.

Regular bugs (wrong detection logic, UI glitches, missing translations, etc.) are **not** security issues — please report those as a normal [GitHub Issue](https://github.com/realsly2/Orphan-Entity-Cleaner/issues) instead.

### Reporting a Vulnerability

Please **do not** open a public GitHub issue for security vulnerabilities. Instead, use GitHub's private reporting:

1. Go to the [Security tab](https://github.com/realsly2/Orphan-Entity-Cleaner/security) of this repository.
2. Click **"Report a vulnerability"** to open a private advisory.

If that's not available to you, you can alternatively open a regular issue asking to be contacted for a private channel, without including exploit details.

### What to expect

This is a hobby project maintained in my spare time, so there is no guaranteed response time (no formal SLA). As a rough guideline:

- I aim to acknowledge new reports within **7 days**.
- If a report is confirmed, I'll work on a fix and publish a new release as soon as reasonably possible, and credit the reporter (unless you'd prefer to stay anonymous).
- If a report is declined (e.g. out of scope, not reproducible, or a Home Assistant Core issue), I'll explain why.

---

## Deutsche Version

### Unterstützte Versionen

Orphan Cleaner ist eine kleine Home-Assistant-Custom-Integration mit nur einem Maintainer. Sicherheitsupdates gibt es ausschließlich für die **jeweils aktuellste veröffentlichte Version**. Ältere Versionen werden nicht mit Sicherheits-Patches versorgt — bitte vor einer Meldung immer erst über HACS auf die neueste Version aktualisieren.

### Geltungsbereich

Orphan Cleaner ist eine **Custom Integration** über HACS, kein Teil von Home Assistant Core und nicht von Home Assistant / Nabu Casa geprüft. Sie läuft mit demselben Vertrauensniveau wie jede andere manuell installierte Custom Integration. Konkret in diesem Geltungsbereich:

- Der Integrations-Code unter `custom_components/orphan_cleaner/` (Services, Config Flow, API-Views).
- Das Sidebar-Panel (`frontend/orphan-cleaner-panel.js`).

Nicht im Geltungsbereich: Schwachstellen in Home Assistant Core selbst, in HACS, oder in Drittanbieter-Abhängigkeiten — bitte direkt beim jeweiligen Projekt melden.

Da diese Integration Entitäten **dauerhaft aus der Entity Registry löschen kann**, zählt als sicherheitsrelevant alles, was Folgendes ermöglichen würde:

- Löschen oder Ändern von Entitäten, ohne dass ein authentifizierter Admin dies bewusst auslöst.
- Umgehen der `require_admin`- bzw. `requires_auth`-Prüfungen am Panel oder an den `/api/orphan_cleaner/*`-Endpunkten.
- Lesen oder Schreiben von Dateien außerhalb des vorgesehenen Home-Assistant-Konfigurationsverzeichnisses (z. B. über den Backup-Export).
- Ausführen von beliebigem Code über das Panel oder einen Service-Aufruf.

Normale Bugs (falsche Erkennungslogik, UI-Fehler, fehlende Übersetzungen usw.) sind **keine** Sicherheitsprobleme — dafür bitte ein normales [GitHub Issue](https://github.com/realsly2/Orphan-Entity-Cleaner/issues) erstellen.

### Eine Schwachstelle melden

Bitte **keine** öffentlichen GitHub Issues für Sicherheitslücken erstellen. Nutze stattdessen die private Meldefunktion von GitHub:

1. Gehe zum [Security-Tab](https://github.com/realsly2/Orphan-Entity-Cleaner/security) dieses Repositories.
2. Klicke auf **"Report a vulnerability"**, um eine private Advisory zu öffnen.

Falls das bei dir nicht verfügbar ist, kannst du alternativ ein normales Issue eröffnen und um einen privaten Kontaktweg bitten, ohne Exploit-Details zu nennen.

### Was du erwarten kannst

Dies ist ein Hobbyprojekt, das in meiner Freizeit gepflegt wird — es gibt daher keine garantierte Reaktionszeit (kein formales SLA). Als grobe Richtschnur:

- Ich versuche, neue Meldungen innerhalb von **7 Tagen** zu bestätigen.
- Wird eine Meldung bestätigt, arbeite ich an einem Fix und veröffentliche so bald wie sinnvoll möglich eine neue Version, und nenne dich als Melder (außer du möchtest anonym bleiben).
- Wird eine Meldung abgelehnt (z. B. außerhalb des Geltungsbereichs, nicht reproduzierbar, oder ein Home-Assistant-Core-Thema), erkläre ich dir warum.
