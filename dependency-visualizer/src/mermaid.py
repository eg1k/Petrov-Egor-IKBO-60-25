"""Визуализация графа зависимостей: язык диаграмм Mermaid и показ изображения.

Текстовое представление строится вручную (без сторонних библиотек).
Изображение показывается в браузере: формируется HTML-страница, на которой
библиотека mermaid.js рисует диаграмму по тексту графа.
"""

import html
import os
import re
import webbrowser

MERMAID_JS = "https://cdn.jsdelivr.net/npm/mermaid@10.9.1/dist/mermaid.min.js"


def _label(text):
    """Подпись узла в кавычках; кавычки внутри заменяются сущностью Mermaid."""
    return '"' + text.replace('"', "#quot;") + '"'


def to_mermaid(graph, reverse=False, direction="TD"):
    """Текст диаграммы Mermaid (flowchart) для графа зависимостей.

    - у каждого узла короткий идентификатор (n0, n1, ...) и подпись с именем
      пакета: имена npm могут содержать '@', '/', '.', недопустимые в id;
    - стрелка A --> B означает «A зависит от B»;
    - для графа обратных зависимостей (reverse=True) рёбра хранятся
      развёрнутыми, поэтому при выводе они снова переворачиваются, чтобы
      стрелки всегда указывали направление зависимости;
    - рёбра, замыкающие циклы, рисуются пунктиром, корневой пакет выделяется.
    """
    ids = {node: f"n{i}" for i, node in enumerate(graph.edges)}
    cycle_edges = set()
    for cycle in graph.cycles:
        cycle_edges.add((cycle[-2], cycle[-1]))

    lines = [f"flowchart {direction}"]
    for node, nid in ids.items():
        lines.append(f"    {nid}[{_label(node)}]")
    for node, children in graph.edges.items():
        for child in children:
            src, dst = (child, node) if reverse else (node, child)
            arrow = "-.->" if (node, child) in cycle_edges else "-->"
            lines.append(f"    {ids[src]} {arrow} {ids[dst]}")
    lines.append("    classDef root fill:#ffd966,stroke:#b45f06,stroke-width:2px")
    lines.append(f"    class {ids[graph.root]} root")
    return "\n".join(lines) + "\n"


def safe_filename(text):
    """Имя файла из имени пакета: '@babel/core@8.1.2' -> 'babel_core_8.1.2'."""
    return re.sub(r"[^0-9A-Za-z._-]+", "_", text).strip("_") or "graph"


def html_page(title, mermaid_text):
    """HTML-страница, отображающая диаграмму с помощью mermaid.js."""
    return f"""<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<title>{html.escape(title)}</title>
<style>
  body {{ font-family: Segoe UI, Arial, sans-serif; margin: 24px; background: #fff; color: #222; }}
  h1 {{ font-size: 20px; }}
  pre {{ background: #f4f4f4; padding: 12px; overflow: auto; }}
  pre.mermaid {{ background: none; padding: 0; }}
  pre.mermaid svg {{ max-width: 100%; height: auto; }}
  body.full pre.mermaid svg {{ max-width: none; }}
  details {{ margin-top: 24px; }}
  label {{ font-size: 14px; }}
</style>
</head>
<body>
<h1>{html.escape(title)}</h1>
<label><input type="checkbox" onchange="document.body.classList.toggle('full', this.checked)">
  реальный размер (по умолчанию граф вписан в окно)</label>
<pre class="mermaid">
{html.escape(mermaid_text)}</pre>
<details><summary>Текст диаграммы Mermaid</summary><pre>{html.escape(mermaid_text)}</pre></details>
<script src="{MERMAID_JS}"></script>
<script>
  mermaid.initialize({{ startOnLoad: true, maxTextSize: 1000000, maxEdges: 5000,
                        flowchart: {{ useMaxWidth: false }} }});
</script>
</body>
</html>
"""


def save_and_show(graph, title, out_dir, reverse=False, show=True):
    """Сохраняет .mmd и .html в out_dir и открывает изображение в браузере.

    Возвращает (текст Mermaid, путь к .mmd, путь к .html).
    """
    # Большие графы удобнее читать слева направо: длинные цепочки не растягиваются вниз.
    text = to_mermaid(graph, reverse=reverse, direction="LR" if len(graph.edges) > 15 else "TD")
    os.makedirs(out_dir, exist_ok=True)
    base = os.path.join(out_dir, safe_filename(("reverse_" if reverse else "") + graph.root))
    mmd_path, html_path = base + ".mmd", base + ".html"
    with open(mmd_path, "w", encoding="utf-8") as f:
        f.write(text)
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_page(title, text))
    if show:
        webbrowser.open("file:///" + os.path.abspath(html_path).replace("\\", "/"))
    return text, mmd_path, html_path
