# ============================================================
#  🌳 Model Family Tree  –  Local Version
#  Single-window desktop app using pywebview (Edge/WebView2)
#  The tree renders inside the app — no external browser needed
# ============================================================

import json
import threading
import requests
import networkx as nx
import webview  # type: ignore  (installed via requirements.txt)
from collections import defaultdict
from typing import Optional
from huggingface_hub import ModelCard

# ── Configuration ────────────────────────────────────────────
DEFAULT_MODEL_ID = "morikomorizz/GRM-2.6-Plus-Primal"
# ─────────────────────────────────────────────────────────────


# ── Cached model card loader ──────────────────────────────────
class CachedModelCard(ModelCard):
    _cache: dict = {}

    @classmethod
    def load(cls, model_id: str, **kwargs) -> "ModelCard":
        if model_id not in cls._cache:
            try:
                cls._cache[model_id] = super().load(model_id, **kwargs)
            except Exception:
                cls._cache[model_id] = None
        return cls._cache[model_id]

    @classmethod
    def clear_cache(cls):
        cls._cache.clear()


# ── Helpers ───────────────────────────────────────────────────
def _js_escape(s: str) -> str:
    """Escape a string for safe use inside a JS single-quoted string."""
    return (s.replace("\\", "\\\\")
             .replace("'", "\\'")
             .replace("\n", " ")
             .replace("\r", ""))


def get_model_names_from_yaml(url: str) -> list:
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            return [line for line in r.content.decode("utf-8", errors="ignore").splitlines()
                    if "/" in line]
    except Exception:
        pass
    return []


def get_license_color(model: str) -> str:
    PERMISSIVE = {"mit", "bsd", "apache-2.0", "openrail"}
    try:
        card = CachedModelCard.load(model)
        if card is None:
            return "#d3d3d3"
        lic = card.data.to_dict().get("license", "").lower()
        return "#90ee90" if any(p in lic for p in PERMISSIVE) else "#f08080"
    except Exception:
        return "#d3d3d3"


def get_model_names(model: str, genealogy: dict,
                    found: Optional[set] = None,
                    visited: Optional[set] = None,
                    log=None) -> set:
    if found is None:
        found = set()
    if visited is None:
        visited = set()
    if model in visited:
        return found
    visited.add(model)

    if log:
        log(f"Visiting: {model}")

    try:
        card = CachedModelCard.load(model)
        if card is None:
            raise ValueError("Model not found or is private")

        d = card.data.to_dict()
        tags: list = []

        if "base_model" in d:
            tags = d["base_model"]
        if "tags" in d and not tags:
            tags = [t for t in d["tags"] if "/" in str(t)]
        if not tags:
            tags = get_model_names_from_yaml(
                f"https://huggingface.co/{model}/blob/main/merge.yml")
        if not tags:
            tags = get_model_names_from_yaml(
                f"https://huggingface.co/{model}/blob/main/mergekit_config.yml")

        if not isinstance(tags, list):
            tags = [tags] if tags else []

        found.add(model)
        if log:
            log(f"  ✓ {len(tags)} parent(s) found")

        for tag in tags:
            genealogy[tag].append(model)
            get_model_names(tag, genealogy, found, visited, log)

    except Exception as e:
        if log:
            log(f"  ✗ {e}")

    return found


# ── pywebview JS API ──────────────────────────────────────────
class Api:
    def __init__(self):
        self._window = None

    def set_window(self, win):
        self._window = win

    def _js(self, code: str):
        if self._window:
            self._window.evaluate_js(code)

    def _log(self, msg: str):
        self._js(f"appendLog('{_js_escape(msg)}')")

    def generate(self, model_id: str):
        """Called from JS when the user clicks Generate."""
        model_id = model_id.strip()
        if not model_id:
            return
        threading.Thread(target=self._do_generate,
                         args=(model_id,), daemon=True).start()

    def _do_generate(self, model_id: str):
        try:
            self._js("setStatus('running')")
            CachedModelCard.clear_cache()

            genealogy: dict = defaultdict(list)
            get_model_names(model_id, genealogy, log=self._log)

            G = nx.DiGraph()
            for parent, children in genealogy.items():
                for child in children:
                    G.add_edge(parent, child)
            if G.number_of_nodes() == 0:
                G.add_node(model_id)

            self._log("\nColouring nodes by license…")
            nodes = []
            for node in G.nodes():
                nodes.append({
                    "id": node,
                    "label": node.replace("/", "\n"),
                    "title": node,
                    "color": get_license_color(node),
                })

            edges = [{"from": src, "to": dst} for src, dst in G.edges()]

            payload = json.dumps({"nodes": nodes, "edges": edges})
            self._js(f"renderTree({payload})")
            self._log(f"\n✅ Done — {len(nodes)} model(s) in tree.")
            self._js("setStatus('done')")

        except Exception as e:
            safe = _js_escape(str(e))
            self._js(f"setStatus('error', '{safe}')")


# ── Embedded HTML / CSS / JS ──────────────────────────────────
HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Model Family Tree</title>
<script src="https://unpkg.com/vis-network@9.1.2/standalone/umd/vis-network.min.js"></script>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: #1a1a2e; color: #e0e0e0;
    font-family: 'Segoe UI', Tahoma, sans-serif;
    display: flex; flex-direction: column; height: 100vh; overflow: hidden;
  }

  /* ── toolbar ── */
  #toolbar {
    display: flex; align-items: center; gap: 10px;
    padding: 10px 14px; background: #16213e;
    border-bottom: 1px solid #2d3a5a; flex-shrink: 0;
  }
  #toolbar-title { font-size: 18px; font-weight: 700; white-space: nowrap; }
  #model-input {
    flex: 1; padding: 7px 11px;
    background: #0f3460; border: 1px solid #4a90d9;
    color: #fff; border-radius: 5px; font-size: 14px;
    outline: none;
  }
  #model-input:focus { border-color: #7ab8f5; }
  #gen-btn {
    padding: 7px 20px; background: #4a90d9; color: #fff;
    border: none; border-radius: 5px; font-size: 14px;
    font-weight: 700; cursor: pointer; white-space: nowrap;
    transition: background .15s;
  }
  #gen-btn:hover:not(:disabled) { background: #357abd; }
  #gen-btn:disabled { background: #444; cursor: not-allowed; color: #999; }

  /* ── main split ── */
  #main {
    display: flex; flex: 1; overflow: hidden;
  }

  /* ── left sidebar ── */
  #sidebar {
    width: 260px; flex-shrink: 0;
    background: #12122a; border-right: 1px solid #2d3a5a;
    display: flex; flex-direction: column; overflow: hidden;
  }
  #sidebar-header {
    padding: 8px 12px; font-size: 11px; font-weight: 700;
    text-transform: uppercase; letter-spacing: .08em;
    color: #7ab; border-bottom: 1px solid #2d3a5a; flex-shrink: 0;
  }
  #log {
    flex: 1; overflow-y: auto; padding: 8px 10px;
    font-family: Consolas, 'Courier New', monospace; font-size: 11.5px;
    color: #9ca3af; white-space: pre-wrap; word-break: break-word;
  }
  #log::-webkit-scrollbar { width: 6px; }
  #log::-webkit-scrollbar-thumb { background: #2d3a5a; border-radius: 3px; }

  /* ── status bar ── */
  #status-bar {
    padding: 5px 12px; font-size: 11.5px; color: #88a;
    background: #12122a; border-top: 1px solid #2d3a5a; flex-shrink: 0;
  }

  /* ── tree canvas ── */
  #tree-wrap {
    flex: 1; position: relative; overflow: hidden;
  }
  #network { width: 100%; height: 100%; }

  /* ── legend ── */
  #legend {
    position: absolute; top: 12px; right: 12px; z-index: 10;
    background: rgba(22,33,62,.92); border: 1px solid #2d3a5a;
    padding: 10px 14px; border-radius: 8px; font-size: 13px;
    line-height: 2;
  }
  .dot {
    display: inline-block; width: 12px; height: 12px;
    border-radius: 3px; margin-right: 6px; vertical-align: middle;
  }

  /* ── empty state ── */
  #empty-state {
    position: absolute; inset: 0; display: flex;
    align-items: center; justify-content: center;
    flex-direction: column; gap: 10px; color: #445;
    font-size: 16px; pointer-events: none;
  }
  #empty-state .big { font-size: 56px; }
</style>
</head>
<body>

<div id="toolbar">
  <span id="toolbar-title">🌳 Model Family Tree</span>
  <input id="model-input" type="text" placeholder="author/model-name"
         value="DEFAULT_MODEL_PLACEHOLDER" />
  <button id="gen-btn" onclick="generate()">Generate ▶</button>
</div>

<div id="main">
  <div id="sidebar">
    <div id="sidebar-header">📋 Log</div>
    <div id="log">Ready. Enter a model ID and click Generate.</div>
    <div id="status-bar" id="status">Idle</div>
  </div>

  <div id="tree-wrap">
    <div id="network"></div>
    <div id="empty-state">
      <span class="big">🌳</span>
      <span>Enter a model ID above to build its family tree</span>
    </div>
    <div id="legend">
      <b>License</b><br>
      <span class="dot" style="background:#90ee90"></span>Permissive<br>
      <span class="dot" style="background:#f08080"></span>Noncommercial<br>
      <span class="dot" style="background:#d3d3d3"></span>Unknown
    </div>
  </div>
</div>

<script>
  let network = null;

  // ── called from Python ──
  function appendLog(msg) {
    const log = document.getElementById('log');
    log.textContent += msg + '\n';
    log.scrollTop = log.scrollHeight;
  }

  function setStatus(state, msg) {
    const btn = document.getElementById('gen-btn');
    const bar = document.getElementById('status-bar');
    if (state === 'running') {
      btn.disabled = true;
      btn.textContent = 'Running…';
      document.getElementById('log').textContent = '';
      bar.textContent = '⏳ Fetching model cards…';
      bar.style.color = '#f0c040';
    } else if (state === 'done') {
      btn.disabled = false;
      btn.textContent = 'Generate ▶';
      bar.textContent = '✅ Complete';
      bar.style.color = '#6ec26e';
    } else if (state === 'error') {
      btn.disabled = false;
      btn.textContent = 'Generate ▶';
      bar.textContent = '❌ ' + (msg || 'Error');
      bar.style.color = '#f08080';
    }
  }

  function renderTree(data) {
    document.getElementById('empty-state').style.display = 'none';
    const container = document.getElementById('network');
    const nodes = new vis.DataSet(data.nodes);
    const edges = new vis.DataSet(data.edges);
    const options = {
      layout: {
        hierarchical: {
          enabled: true, direction: 'UD',
          sortMethod: 'directed',
          nodeSpacing: 220, levelSeparation: 180
        }
      },
      physics: { enabled: false },
      edges: {
        arrows: { to: { enabled: true } },
        color: { color: '#6677aa' },
        smooth: { type: 'cubicBezier' }
      },
      nodes: {
        shape: 'box',
        font: { size: 13, color: '#111' },
        borderWidth: 2,
        borderWidthSelected: 3
      },
      interaction: {
        hover: true, navigationButtons: true, keyboard: true,
        tooltipDelay: 200
      }
    };
    if (network) network.destroy();
    network = new vis.Network(container, { nodes, edges }, options);
  }

  // ── called from user ──
  function generate() {
    const modelId = document.getElementById('model-input').value.trim();
    if (!modelId) return;
    window.pywebview.api.generate(modelId);
  }

  document.getElementById('model-input').addEventListener('keydown', e => {
    if (e.key === 'Enter') generate();
  });
</script>
</body>
</html>
""".replace("DEFAULT_MODEL_PLACEHOLDER", DEFAULT_MODEL_ID)


# ── Entry point ───────────────────────────────────────────────
if __name__ == "__main__":
    api = Api()
    win = webview.create_window(
        title="Model Family Tree",
        html=HTML,
        js_api=api,
        width=1200,
        height=750,
        min_size=(700, 480),
    )
    api.set_window(win)
    webview.start(debug=False)
