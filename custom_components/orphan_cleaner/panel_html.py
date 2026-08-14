PANEL_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Orphan Cleaner</title>
  <style>
    body { font-family: system-ui, sans-serif; margin: 16px; color: #222; }
    .row { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
    input, button { padding: 8px; }
    input[type="text"] { min-width: 280px; }
    table { width: 100%; border-collapse: collapse; margin-top: 12px; }
    th, td { border-bottom: 1px solid #ddd; padding: 8px; text-align: left; vertical-align: top; }
    th { background: #f7f7f7; }
    .muted { color: #666; }
    .danger { color: #b00020; }
    .ok { color: #0a7a0a; }
    .toolbar { margin-bottom: 12px; }
    .spacer { flex: 1; }
    .small { font-size: 12px; }
  </style>
</head>
<body>
  <h2>Orphan Cleaner</h2>

  <div class="row toolbar">
    <button onclick="scan()">Scan</button>
    <button onclick="refreshResults()">Refresh</button>
    <button onclick="backup()">Backup</button>
    <button onclick="exportResults()">Export</button>
    <button onclick="clearResults()">Clear</button>
    <button class="danger" onclick="deleteSelected()">Delete Selected</button>
    <span class="spacer"></span>
    <input id="q" type="text" placeholder="Search entity_id, name, platform" oninput="render()" />
  </div>

  <div class="row toolbar">
    <button onclick="selectVisible(true)">Select Visible</button>
    <button onclick="selectVisible(false)">Unselect Visible</button>
    <span id="status" class="muted">Idle</span>
  </div>

  <div id="app"></div>

<script>
let results = [];

async function api(path, body) {
  const opts = {
    method: body ? "POST" : "GET",
    headers: body ? {"Content-Type":"application/json"} : {}
  };
  if (body) opts.body = JSON.stringify(body);
  const r = await fetch(path, opts);
  try { return await r.json(); } catch { return {}; }
}

function filtered() {
  const q = document.getElementById("q").value.toLowerCase().trim();
  return results.filter(x =>
    !q ||
    (x.entity_id || "").toLowerCase().includes(q) ||
    (x.name || "").toLowerCase().includes(q) ||
    (x.platform || "").toLowerCase().includes(q)
  );
}

function render() {
  const rows = filtered();
  document.getElementById("status").textContent = `${rows.length} shown / ${results.length} total`;
  document.getElementById("app").innerHTML = `
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
        ${rows.map(x => `
          <tr>
            <td><input type="checkbox" data-entity="${x.entity_id}"></td>
            <td>${x.entity_id || ""}</td>
            <td>${x.name || ""}</td>
            <td>${x.platform || ""}</td>
            <td>${x.reason || ""}</td>
            <td class="small">${x.config_entry_id || ""}</td>
            <td class="small">${x.device_id || ""}</td>
          </tr>
        `).join("")}
      </tbody>
    </table>`;
}

function visibleCheckboxes() {
  return [...document.querySelectorAll("tbody input[type=checkbox]")];
}

function selectVisible(state) {
  visibleCheckboxes().forEach(cb => cb.checked = state);
}

async function refreshResults() {
  results = await api("/api/orphan_cleaner/results");
  if (!Array.isArray(results)) results = [];
  render();
}

async function scan() {
  await api("/api/services/orphan_cleaner/scan", {});
  await refreshResults();
}

async function backup() {
  await api("/api/services/orphan_cleaner/backup_results", {});
}

async function exportResults() {
  await api("/api/services/orphan_cleaner/export_results", {});
  document.getElementById("status").textContent = "Export stored";
}

async function clearResults() {
  await api("/api/services/orphan_cleaner/clear_results", {});
  results = [];
  render();
}

async function deleteSelected() {
  const ids = [...document.querySelectorAll("input[type=checkbox]:checked")].map(x => x.dataset.entity);
  if (!ids.length) {
    document.getElementById("status").textContent = "No entities selected";
    return;
  }
  await api("/api/services/orphan_cleaner/delete_selected", { entity_ids: ids });
  await refreshResults();
}

refreshResults();
</script>
</body>
</html>
"""
