---
license: mit
tags:
  - model-family-tree
  - huggingface
  - visualization
  - tools
language:
  - en
---

# 🌳 Model Family Tree — Local Desktop App

Automatically traces and visualises the **family tree of any Hugging Face model** in a single self-contained desktop window — no browser or external viewer needed.

Nodes are colour-coded by license type. The tree is interactive: zoom, pan, and hover over any node to see its full model ID.

> ⚠️ **This is a desktop application** (requires Python on your machine).  
> It is distributed as a code repository, not a Hugging Face Space.  
> For the original hosted web version, see [mlabonne/model-family-tree](https://huggingface.co/spaces/mlabonne/model-family-tree).

---

## Credits

| Contributor | Contribution |
|---|---|
| Thanks to mlabonne and leonardlin for the original code and adaptation this python app was based on.
| [thebrinkster](https://huggingface.co/thebrinkster) | Wrapped original backend code in Tkinter and adapted it to run locally from a Google Colab notebook that can be found (https://colab.research.google.com/drive/1s2eQlolcI1VGgDhqWIANfkfKvcKrMyNr?usp=sharing#scrollTo=lIYdn1woOS1n).
| 
| [mlabonne](https://huggingface.co/mlabonne) | Original concept, core genealogy logic, and the Colab / HF Space this is adapted from |
| [leonardlin](https://huggingface.co/leonardlin) | Original caching implementation for model cards |
| This repo | Local desktop adaptation — pywebview single-window GUI, vis.js rendering, cross-platform packaging |

**Third-party libraries used:**

| Library | License | Purpose |
|---|---|---|
| [vis-network](https://github.com/visjs/vis-network) | Apache 2.0 | Interactive tree rendering |
| [pywebview](https://github.com/r0x0r/pywebview) | BSD 3-Clause | Native desktop window (Edge/WebKit) |
| [networkx](https://github.com/networkx/networkx) | BSD 3-Clause | Graph construction |
| [huggingface_hub](https://github.com/huggingface/huggingface_hub) | Apache 2.0 | Model card fetching |
| [requests](https://github.com/psf/requests) | Apache 2.0 | HTTP requests for merge YAML files |

---

## Prerequisites

- Python 3.8+
- `pip` (comes with Python)
- Internet connection (to fetch model cards from Hugging Face)

**Platform support:**

| OS | Web engine used | Extra install? |
|---|---|---|
| Windows 10/11 | Edge WebView2 (built-in) | None |
| macOS | WKWebView (built-in) | None |
| Linux | GTK WebKit2 | `sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0 gir1.2-webkit2-4.0` |

---

## Setup (one time only)

```bash
pip install -r requirements.txt
```

---

## Running

```bash
python model_tree.py
```

A single desktop window opens with everything inside it:

| Area | Purpose |
|---|---|
| **Top bar** | Model ID input field + Generate button |
| **Left panel** | Live log — shows each model as it's fetched |
| **Main canvas** | Interactive vis.js family tree |
| **Status bar** | Shows idle / running / done / error state |

### Steps
1. Type a Hugging Face model ID into the input box (e.g. `mistralai/Mistral-7B-v0.1`)
2. Click **Generate ▶** or press **Enter**
3. Watch the log panel as models are fetched
4. The tree appears in the main canvas when complete — zoom, pan, click nodes freely
5. Clear the input, type a new model, and generate again any time

---

## Legend

| Colour | Meaning |
|---|---|
| 🟢 Green | Permissive license (MIT, BSD, Apache-2.0, OpenRAIL) |
| 🔴 Red/Coral | Noncommercial or restrictive license |
| ⬜ Gray | License unknown or model card not found |

---

## Tips

- Large trees can take a minute or two — watch the live log.
- The cache is cleared automatically on each new Generate run.
- The default model ID can be changed by editing `DEFAULT_MODEL_ID` at the top of `model_tree.py`.

---

## License

MIT — see [LICENSE](./LICENSE) for full text and third-party attributions.
