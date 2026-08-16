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

class OrphanCleanerPanel extends HTMLElement {
  constructor() {
    super();
    this._results = [];
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
        input, button { padding: 8px; font-size: 14px; }
        input[type="text"] { min-width: 280px; }
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
      </style>
      <div class="oc-wrap">
        <h2>Orphan Cleaner</h2>

        <div class="oc-row oc-toolbar">
          <button id="oc-scan">Scan</button>
          <button id="oc-refresh">Refresh</button>
          <button id="oc-backup">Backup</button>
          <button id="oc-export">Export</button>
          <button id="oc-clear">Clear</button>
          <button id="oc-delete" class="oc-danger">Delete Selected</button>
          <span class="oc-spacer"></span>
          <input id="oc-q" type="text" placeholder="Search entity_id, name, platform" />
        </div>

        <div class="oc-row oc-toolbar">
          <button id="oc-select-all">Select Visible</button>
          <button id="oc-unselect-all">Unselect Visible</button>
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
    this.querySelector("#oc-q").addEventListener("input", () => this._render());
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
    return this._results.filter(
      (x) =>
        !q ||
        (x.entity_id || "").toLowerCase().includes(q) ||
        (x.name || "").toLowerCase().includes(q) ||
        (x.platform || "").toLowerCase().includes(q)
    );
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
            <th>Reason</th>
            <th>Config Entry ID</th>
            <th>Device ID</th>
          </tr>
        </thead>
        <tbody>
          ${rows
            .map(
              (x) => `
            <tr>
              <td><input type="checkbox" data-entity="${x.entity_id}"></td>
              <td>${x.entity_id || ""}</td>
              <td>${x.name || ""}</td>
              <td>${x.platform || ""}</td>
              <td>${x.reason || ""}</td>
              <td class="oc-small">${x.config_entry_id || ""}</td>
              <td class="oc-small">${x.device_id || ""}</td>
            </tr>
          `
            )
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
      } else if (payload && Array.isArray(payload.results)) {
        this._results = payload.results;
      } else {
        this._results = [];
      }
    } catch (err) {
      this._results = [];
      this._setStatus(`Error loading results: ${err}`);
      return;
    }
    this._render();
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
      this._setStatus("Backup created");
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
      `Delete ${ids.length} selected entities? This cannot be undone (except via backup).`
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
  }
}

customElements.define("orphan-cleaner-panel", OrphanCleanerPanel);
