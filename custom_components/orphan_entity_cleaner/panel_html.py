# custom_components/orphan_entity_cleaner/panel_html.py
PANEL_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Orphan Entity Cleaner</title>
  <style>
    body { font-family: sans-serif; margin: 16px; }
    button { margin: 4px; }
    input { width: 100%; max-width: 420px; padding: 8px; margin: 8px 0; }
    .row { padding: 8px; border-bottom: 1px solid #ddd; }
  </style>
</head>
<body>
  <h2>Orphan Entity Cleaner</h2>
  <input id="search" placeholder="Filter by entity id, name, or platform">
  <div>
    <button onclick="loadResults()">Refresh</button>
    <button onclick="scan()">Scan</button>
    <button onclick="clearResults()">Clear</button>
  </div>
  <div id="results"></div>

  <script>
    async function loadResults() {
      const res = await fetch('/api/orphan_entity_cleaner/results');
      const data = await res.json();
      const q = document.getElementById('search').value.toLowerCase();
      const root = document.getElementById('results');
      root.innerHTML = '';
      (data.results || []).filter(item =>
        !q ||
        item.entity_id.toLowerCase().includes(q) ||
        (item.name || '').toLowerCase().includes(q) ||
        (item.platform || '').toLowerCase().includes(q)
      ).forEach(item => {
        const div = document.createElement('div');
        div.className = 'row';
        div.innerHTML = `<strong>${item.entity_id}</strong><br>${item.name || ''}<br>${item.platform || ''}<br>${item.reason || ''}`;
        root.appendChild(div);
      });
    }

    async function scan() {
      await fetch('/api/services/orphan_entity_cleaner/scan', { method: 'POST', headers: {'Content-Type':'application/json'}, body: '{}' });
      loadResults();
    }

    async function clearResults() {
      await fetch('/api/services/orphan_entity_cleaner/clear_results', { method: 'POST', headers: {'Content-Type':'application/json'}, body: '{}' });
      loadResults();
    }

    document.getElementById('search').addEventListener('input', loadResults);
    loadResults();
  </script>
</body>
</html>
"""
