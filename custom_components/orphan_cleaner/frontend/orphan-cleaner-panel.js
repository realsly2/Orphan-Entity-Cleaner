// custom_components/orphan_cleaner/frontend/orphan-cleaner-panel.js
//
// Panel-Custom-Element für Orphan Cleaner.
//
// Wichtig: Home Assistant setzt auf dieses Element die Property `hass`
// (nicht ein HTML-Attribut). Dieses hass-Objekt ist bereits authentifiziert -
// hass.callService() / hass.callApi() hängen den Bearer-Token automatisch an.
// Dadurch brauchen wir hier keine eigene fetch()/Token-Logik mehr, im
// Unterschied zum vorherigen iframe-Ansatz (der still mit 401 gescheitert
// wäre, da HAs /api/* Endpunkte weder Cookies noch unauthentifizierte
// iframe-Navigation akzeptieren).

const REASON_INFO = {
  no_config_or_device: {
    label: "Keine Verknüpfung",
    badge: "⚠️ Prüfen",
    badgeClass: "oc-badge-warn",
    hint: "Kann bei YAML-Helfern, Template-Sensoren, Gruppen oder Zonen normal sein - die haben nie eine config_entry_id/device_id. Vor dem Löschen prüfen, ob der Entity-Name/die Domain dir bekannt vorkommt.",
  },
  platform_without_device: {
    label: "Plattform ohne Geräte-ID",
    badge: "⚠️ Prüfen",
    badgeClass: "oc-badge-warn",
    hint: "Zusatzwarnung aus dem strict_mode. Manche Integrationen legen bewusst kein Geräte-Objekt an - allein deswegen nicht automatisch löschen.",
  },
  disabled_long_term: {
    label: "Lange deaktiviert",
    badge: "🟠 Manuell deaktiviert",
    badgeClass: "oc-badge-orange",
    hint: "Du (oder jemand) hat diese Entität selbst deaktiviert. Das kann Absicht sein (z.B. saisonal pausiert) - vor dem Löschen kurz überlegen, warum sie deaktiviert wurde.",
  },
  pending_purge_by_ha: {
    label: "Wird von HA entfernt",
    badge: "✅ Kein Handlungsbedarf",
    badgeClass: "oc-badge-ok",
    hint: "Home Assistant hat diese Entität bereits selbst als gelöscht markiert und entfernt sie automatisch nach ca. 30 Tagen endgültig. Nicht über dieses Tool löschbar, rein informativ.",
  },
};

function reasonInfo(code) {
  return (
    REASON_INFO[code] || {
      label: code,
      badge: "",
      badgeClass: "",
      hint: "",
    }
  );
}

class OrphanCleanerPanel extends HTMLElement {
  constructor() {
    super();
    this._results = [];
    this._backups = [];
    this._lastBackupPath = null;
    this._lastRestore = null;
    this._built = false;
  }

  set hass(hass) {
    this._hass = hass;
    if (!this._built) {
      this._built = true;
      this._build();
      this._refreshResults();
    }
  }

  get hass() {
    return this._hass;
  }

  _build() {
    this.innerHTML = `
      <style>
        :host { display: block; }
        .oc-wrap {
          font-family: var(--paper-font-body1_-_font-family, system-ui, sans-serif);
          padding: 16px;
          color: var(--primary-text-color, #222);
        }
        .oc-row { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
        .oc-toolbar { margin-bottom: 12px; }
        input, button, select { padding: 8px; font-size: 14px; }
        input[type="text"] { min-width: 240px; }
        table { width: 100%; border-collapse: collapse; margin-top: 12px; }
        th, td {
          border-bottom: 1px solid var(--divider-color, #ddd);
          padding: 8px;
          text-align: left;
          vertical-align: top;
        }
        th { background: var(--secondary-background-color, #f7f7f7); }
        .oc-muted { color: var(--secondary-text-color, #666); }
        .oc-danger { color: #b00020; }
        .oc-spacer { flex: 1; }
        .oc-small { font-size: 12px; }
        .oc-badge {
          display: inline-block;
          padding: 2px 6px;
          border-radius: 4px;
          font-size: 12px;
          white-space: nowrap;
        }
        .oc-badge-warn { background: #fff3cd; color: #7a5b00; }
        .oc-badge-orange { background: #ffe0cc; color: #8a3d00; }
        .oc-badge-ok { background: #d9f2df; color: #1e6b34; }
        .oc-hint { display: block; font-size: 12px; color: var(--secondary-text-color, #666); margin-top: 2px; }
        .oc-note {
          background: var(--secondary-background-color, #f7f7f7);
          border-left: 3px solid #93c5fd;
          padding: 8px 12px;
          margin-bottom: 12px;
          font-size: 13px;
        }
      </style>
      <div class="oc-wrap">
        <h2>Orphan Cleaner</h2>

        <div class="oc-note">
          Backups liegen als JSON im Unterordner
          <code>orphan_cleaner_backups/</code> deines Home-Assistant-Konfigurationsordners
          (also z.B. <code>/config/orphan_cleaner_backups/</code>), nicht direkt im
          config-Root. Jede Backup-Datei enthält alle Infos, um die Entität bei Bedarf
          wiederherzustellen. "Backups anzeigen" listet vorhandene Dateien auf, daneben
          gibt es je Datei einen Restore-Button.
        </div>

        <div class="oc-row oc-toolbar">
          <button id="oc-scan">Scan</button>
          <button id="oc-refresh">Refresh</button>
          <button id="oc-backup">Backup</button>
          <button id="oc-export">Export</button>
          <button id="oc-clear">Clear</button>
          <button id="oc-delete" class="oc-danger">Delete Selected</button>
          <button id="oc-list-backups">Backups anzeigen</button>
        </div>

        <div id="oc-backups-section" style="display:none;">
          <table>
            <thead>
              <tr>
                <th>Datei</th>
                <th>Zeitpunkt</th>
                <th>Typ</th>
                <th>Anzahl Einträge</th>
                <th></th>
              </tr>
            </thead>
            <tbody id="oc-backups-body"></tbody>
          </table>
        </div>

        <div id="oc-restore-status" class="oc-note" style="display:none;"></div>

        <div class="oc-row oc-toolbar">
          <input id="oc-q" type="text" placeholder="Suche: entity_id, name, platform" />
          <select id="oc-reason-filter">
            <option value="">Alle Gründe</option>
            <option value="no_config_or_device">Keine Verknüpfung</option>
            <option value="platform_without_device">Plattform ohne Geräte-ID</option>
            <option value="disabled_long_term">Lange deaktiviert</option>
            <option value="pending_purge_by_ha">Wird von HA entfernt</option>
          </select>
          <label class="oc-small">
            <input type="checkbox" id="oc-hide-pending" /> "Wird von HA entfernt" ausblenden
          </label>
        </div>

        <div class="oc-row oc-toolbar">
          <button id="oc-select-all">Select Visible</button>
          <button id="oc-unselect-all">Unselect Visible</button>
          <span class="oc-spacer"></span>
          <span id="oc-status" class="oc-muted">Idle</span>
        </div>

        <div id="oc-app"></div>
      </div>
    `;

    this.querySelector("#oc-scan").addEventListener("click", () => this._scan());
    this.querySelector("#oc-refresh").addEventListener("click", () => this._refreshResults());
    this.querySelector("#oc-backup").addEventListener("click", () => this._backup());
    this.querySelector("#oc-export").addEventListener("click", () => this._exportResults());
    this.querySelector("#oc-clear").addEventListener("click", () => this._clearResults());
    this.querySelector("#oc-delete").addEventListener("click", () => this._deleteSelected());
    this.querySelector("#oc-list-backups").addEventListener("click", () => this._listBackups());
    this.querySelector("#oc-q").addEventListener("input", () => this._render());
    this.querySelector("#oc-reason-filter").addEventListener("change", () => this._render());
    this.querySelector("#oc-hide-pending").addEventListener("change", () => this._render());
    this.querySelector("#oc-select-all").addEventListener("click", () => this._selectVisible(true));
    this.querySelector("#oc-unselect-all").addEventListener("click", () => this._selectVisible(false));
  }

  _setStatus(text) {
    const el = this.querySelector("#oc-status");
    if (el) el.textContent = text;
  }

  _filtered() {
    const qInput = this.querySelector("#oc-q");
    const q = (qInput && qInput.value ? qInput.value : "").toLowerCase().trim();
    const reasonFilter = this.querySelector("#oc-reason-filter").value;
    const hidePending = this.querySelector("#oc-hide-pending").checked;

    return this._results.filter((x) => {
      if (hidePending && x.pending_purge) return false;
      if (reasonFilter && !(x.orphaned_reason || []).includes(reasonFilter)) return false;
      if (!q) return true;
      return (
        (x.entity_id || "").toLowerCase().includes(q) ||
        (x.name || "").toLowerCase().includes(q) ||
        (x.platform || "").toLowerCase().includes(q)
      );
    });
  }

  _render() {
    const rows = this._filtered();
    this._setStatus(`${rows.length} shown / ${this._results.length} total`);
    this.querySelector("#oc-app").innerHTML = `
      <table>
        <thead>
          <tr>
            <th></th>
            <th>Entity</th>
            <th>Name</th>
            <th>Platform</th>
            <th>Grund</th>
            <th>Config Entry ID</th>
            <th>Device ID</th>
          </tr>
        </thead>
        <tbody>
          ${rows
            .map((x) => {
              const reasons = x.orphaned_reason && x.orphaned_reason.length ? x.orphaned_reason : [x.reason];
              const badges = reasons
                .map((code) => {
                  const info = reasonInfo(code);
                  return `<span class="oc-badge ${info.badgeClass}" title="${info.hint}">${info.badge || info.label}</span>`;
                })
                .join(" ");
              const hints = reasons
                .map((code) => reasonInfo(code).hint)
                .filter(Boolean);
              return `
            <tr>
              <td>${x.pending_purge ? "" : `<input type="checkbox" data-entity="${x.entity_id}">`}</td>
              <td>${x.entity_id || ""}</td>
              <td>${x.name || ""}</td>
              <td>${x.platform || ""}</td>
              <td>
                ${badges}
                ${hints[0] ? `<span class="oc-hint">${hints[0]}</span>` : ""}
              </td>
              <td class="oc-small">${x.config_entry_id || ""}</td>
              <td class="oc-small">${x.device_id || ""}</td>
            </tr>
          `;
            })
            .join("")}
        </tbody>
      </table>`;
  }

  _visibleCheckboxes() {
    return [...this.querySelectorAll("tbody input[type=checkbox]")];
  }

  _selectVisible(state) {
    this._visibleCheckboxes().forEach((cb) => (cb.checked = state));
  }

  async _refreshResults() {
    this._setStatus("Loading...");
    try {
      const payload = await this.hass.callApi("GET", "orphan_cleaner/results");
      if (Array.isArray(payload)) {
        this._results = payload;
        this._backups = [];
        this._lastBackupPath = null;
        this._lastRestore = null;
      } else if (payload && Array.isArray(payload.results)) {
        this._results = payload.results;
        this._backups = payload.backups || [];
        this._lastBackupPath = payload.last_backup_path || null;
        this._lastRestore = payload.last_restore || null;
      } else {
        this._results = [];
        this._backups = [];
        this._lastBackupPath = null;
        this._lastRestore = null;
      }
    } catch (err) {
      this._results = [];
      this._setStatus(`Error loading results: ${err}`);
      return;
    }
    this._render();
    if (this._backups && this._backups.length) {
      this._renderBackups();
    }
  }

  async _scan() {
    this._setStatus("Scanning...");
    try {
      await this.hass.callService("orphan_cleaner", "scan", {});
    } catch (err) {
      this._setStatus(`Scan failed: ${err}`);
      return;
    }
    await this._refreshResults();
  }

  async _backup() {
    this._setStatus("Backing up...");
    try {
      await this.hass.callService("orphan_cleaner", "backup_results", {});
      await this._refreshResults();
      this._setStatus(
        this._lastBackupPath ? `Backup erstellt: ${this._lastBackupPath}` : "Backup created"
      );
    } catch (err) {
      this._setStatus(`Backup failed: ${err}`);
    }
  }

  async _exportResults() {
    try {
      await this.hass.callService("orphan_cleaner", "export_results", {});
      this._setStatus("Export stored");
    } catch (err) {
      this._setStatus(`Export failed: ${err}`);
    }
  }

  async _clearResults() {
    try {
      await this.hass.callService("orphan_cleaner", "clear_results", {});
      this._results = [];
      this._render();
    } catch (err) {
      this._setStatus(`Clear failed: ${err}`);
    }
  }

  async _deleteSelected() {
    const ids = this._visibleCheckboxes()
      .filter((cb) => cb.checked)
      .map((cb) => cb.dataset.entity);

    if (!ids.length) {
      this._setStatus("No entities selected");
      return;
    }

    const confirmed = window.confirm(
      `${ids.length} ausgewählte Entitäten löschen? Home Assistant verschiebt sie zunächst ` +
        `für ca. 30 Tage in einen internen "gelöscht, wartet auf endgültiges Entfernen"-Zustand ` +
        `(daher zusätzlich das Backup - sicherer Weg, um alle nötigen Infos für eine spätere ` +
        `Wiederherstellung zu haben).`
    );
    if (!confirmed) return;

    this._setStatus("Deleting...");
    try {
      await this.hass.callService("orphan_cleaner", "delete_selected", { entity_ids: ids });
    } catch (err) {
      this._setStatus(`Delete failed: ${err}`);
      return;
    }
    await this._refreshResults();
    if (this._lastBackupPath) {
      this._setStatus(`Gelöscht. Backup: ${this._lastBackupPath}`);
    }
  }

  async _listBackups() {
    this._setStatus("Lade Backups...");
    try {
      await this.hass.callService("orphan_cleaner", "list_backups", {});
    } catch (err) {
      this._setStatus(`Backups laden fehlgeschlagen: ${err}`);
      return;
    }
    await this._refreshResults();
    this.querySelector("#oc-backups-section").style.display = "block";
    this._renderBackups();
    this._setStatus(`${(this._backups || []).length} Backup(s) gefunden`);
  }

  _renderBackups() {
    const section = this.querySelector("#oc-backups-section");
    const body = this.querySelector("#oc-backups-body");
    if (!section || !body) return;

    section.style.display = "block";
    body.innerHTML = (this._backups || [])
      .map(
        (b) => `
        <tr>
          <td class="oc-small">${b.filename || ""}</td>
          <td class="oc-small">${b.timestamp || ""}</td>
          <td class="oc-small">${b.type || ""}</td>
          <td class="oc-small">${b.count ?? ""}</td>
          <td><button class="oc-restore-btn" data-filename="${b.filename}">Restore</button></td>
        </tr>
      `
      )
      .join("");

    body.querySelectorAll(".oc-restore-btn").forEach((btn) => {
      btn.addEventListener("click", () => this._restoreBackup(btn.dataset.filename));
    });
  }

  async _restoreBackup(filename) {
    const confirmed = window.confirm(
      `Aus "${filename}" wiederherstellen? Es werden nur Entitäten erzeugt, die aktuell noch ` +
        `nicht existieren - vorhandene Entitäten bleiben unangetastet. Zustandsverlauf, ` +
        `Bereich und Icon werden dabei NICHT wiederhergestellt (nur entity_id, Name, ` +
        `Plattform-Zuordnung).`
    );
    if (!confirmed) return;

    this._setStatus("Stelle wieder her...");
    try {
      await this.hass.callService("orphan_cleaner", "restore_from_backup", { filename });
    } catch (err) {
      this._setStatus(`Restore failed: ${err}`);
      return;
    }
    await this._refreshResults();
    const restoreStatusEl = this.querySelector("#oc-restore-status");
    if (this._lastRestore && restoreStatusEl) {
      const r = this._lastRestore;
      restoreStatusEl.style.display = "block";
      restoreStatusEl.innerHTML =
        `<strong>Restore-Ergebnis (${filename}):</strong> ` +
        `${(r.restored || []).length} wiederhergestellt, ` +
        `${(r.skipped_existing || []).length} übersprungen (existieren bereits), ` +
        `${(r.errors || []).length} Fehler.` +
        ((r.restored || []).length ? `<br>Wiederhergestellt: ${r.restored.join(", ")}` : "");
    }
    this._setStatus("Restore abgeschlossen");
  }
}

customElements.define("orphan-cleaner-panel", OrphanCleanerPanel);
