#!/usr/bin/env python3
from __future__ import annotations

import os
from pathlib import Path
from collections import defaultdict

# Diretórios ignorados (padrão corporativo)
IGNORE_DIRS = {
    ".git", ".github", "node_modules", "vendor", "bin", "obj", ".idea", ".vscode",
    "dist", "build", ".next", ".nuxt", "coverage", ".terraform"
}

# Mapa simples extensão -> linguagem (ajuste livre)
EXT_TO_LANG = {
    ".cs": "C#",
    ".csproj": "MSBuild",
    ".sln": "MSBuild",
    ".php": "PHP",
    ".sql": "SQL",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".jsx": "JavaScript",
    ".json": "JSON",
    ".yml": "YAML",
    ".yaml": "YAML",
    ".md": "Markdown",
    ".html": "HTML",
    ".css": "CSS",
    ".scss": "SCSS",
    ".sh": "Shell",
    ".ps1": "PowerShell",
    ".dockerfile": "Dockerfile",
}

# Alguns arquivos sem extensão
FILENAME_TO_LANG = {
    "dockerfile": "Dockerfile",
    "makefile": "Makefile",
}

def should_ignore(path: Path) -> bool:
    parts = {p.lower() for p in path.parts}
    return any(d.lower() in parts for d in IGNORE_DIRS)

def detect_lang(path: Path) -> str | None:
    name_lower = path.name.lower()
    if name_lower in FILENAME_TO_LANG:
        return FILENAME_TO_LANG[name_lower]

    # Trata Dockerfile sem extensão
    if path.name == "Dockerfile":
        return "Dockerfile"

    ext = path.suffix.lower()
    return EXT_TO_LANG.get(ext)

def human_pct(x: float) -> str:
    return f"{x:.1f}%"

def render_svg(data: list[tuple[str,int]], total: int, out_path: Path) -> None:
    # Config visual (sem dependências)
    width = 900
    height = 280
    padding = 24
    bar_x = padding
    bar_y = 110
    bar_w = width - padding * 2
    bar_h = 18

    title = "Linguagens mais usadas (varredura do repositório)"
    subtitle = "Calculado por tamanho de arquivos versionados (ignorando pastas de build/deps)."

    # Cores simples por linguagem (ajuste livre)
    colors = {
        "C#": "#178600",
        "PHP": "#4F5D95",
        "SQL": "#e38c00",
        "TypeScript": "#2b7489",
        "JavaScript": "#f1e05a",
        "HTML": "#e34c26",
        "CSS": "#563d7c",
        "YAML": "#cb171e",
        "JSON": "#292929",
        "Markdown": "#083fa1",
        "Shell": "#89e051",
        "PowerShell": "#012456",
        "Dockerfile": "#384d54",
        "MSBuild": "#563d7c",
        "Other": "#6b7280",
    }

    # Top 7 no card; resto como "Other"
    top = data[:7]
    other_bytes = sum(b for _, b in data[7:])
    if other_bytes > 0:
        top.append(("Other", other_bytes))

    # Construção do SVG
    def esc(s: str) -> str:
        return (s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
                 .replace('"',"&quot;").replace("'","&apos;"))

    # Barra segmentada
    segments = []
    cursor = 0.0
    for lang, bytes_ in top:
        frac = bytes_ / total if total else 0.0
        seg_w = bar_w * frac
        if seg_w < 1:
            continue
        segments.append((cursor, seg_w, colors.get(lang, colors["Other"])))
        cursor += seg_w

    # Lista textual (lado esquerdo)
    lines = []
    for lang, bytes_ in top:
        pct = (bytes_ / total * 100) if total else 0.0
        lines.append((lang, human_pct(pct), bytes_))

    # Formata bytes em KB/MB
    def fmt_bytes(n: int) -> str:
        if n < 1024:
            return f"{n} B"
        kb = n / 1024
        if kb < 1024:
            return f"{kb:.1f} KB"
        mb = kb / 1024
        if mb < 1024:
            return f"{mb:.1f} MB"
        gb = mb / 1024
        return f"{gb:.2f} GB"

    y0 = 150
    dy = 20

    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" role="img" aria-label="{esc(title)}">')
    svg.append('<defs>')
    svg.append('<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">')
    svg.append('<stop offset="0%" stop-color="#0b1020"/>')
    svg.append('<stop offset="100%" stop-color="#0a0f1c"/>')
    svg.append('</linearGradient>')
    svg.append('</defs>')
    svg.append(f'<rect width="{width}" height="{height}" fill="url(#bg)" rx="18" />')

    svg.append(f'<text x="{padding}" y="44" fill="#ffffff" font-size="20" font-family="Inter,Segoe UI,Arial,sans-serif" font-weight="700">{esc(title)}</text>')
    svg.append(f'<text x="{padding}" y="70" fill="#cbd5e1" font-size="12" font-family="Inter,Segoe UI,Arial,sans-serif">{esc(subtitle)}</text>')

    # Barra total
    svg.append(f'<rect x="{bar_x}" y="{bar_y}" width="{bar_w}" height="{bar_h}" fill="#1f2937" rx="9" />')
    for x, w, c in segments:
        svg.append(f'<rect x="{bar_x + x:.2f}" y="{bar_y}" width="{w:.2f}" height="{bar_h}" fill="{c}" rx="9" />')

    # Legend
    svg.append(f'<text x="{padding}" y="{y0-10}" fill="#e5e7eb" font-size="12" font-family="Inter,Segoe UI,Arial,sans-serif" font-weight="700">Top linguagens</text>')
    for i, (lang, pct, bytes_) in enumerate(lines):
        y = y0 + i * dy
        c = colors.get(lang, colors["Other"])
        svg.append(f'<rect x="{padding}" y="{y-10}" width="10" height="10" fill="{c}" rx="2" />')
        svg.append(f'<text x="{padding+18}" y="{y}" fill="#e5e7eb" font-size="12" font-family="Inter,Segoe UI,Arial,sans-serif">{esc(lang)}</text>')
        svg.append(f'<text x="{width - padding - 180}" y="{y}" fill="#cbd5e1" font-size="12" font-family="Inter,Segoe UI,Arial,sans-serif">{esc(pct)}</text>')
        svg.append(f'<text x="{width - padding - 90}" y="{y}" fill="#94a3b8" font-size="12" font-family="Inter,Segoe UI,Arial,sans-serif">{esc(fmt_bytes(bytes_))}</text>')

    svg.append('</svg>')

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(svg), encoding="utf-8")

def main() -> None:
    root = Path(".").resolve()
    totals = defaultdict(int)

    for p in root.rglob("*"):
        if p.is_dir():
            continue
        if should_ignore(p):
            continue

        lang = detect_lang(p)
        if not lang:
            continue

        try:
            size = p.stat().st_size
        except OSError:
            continue

        # Ignora arquivos vazios
        if size <= 0:
            continue

        totals[lang] += size

    # Ordena por tamanho
    items = sorted(totals.items(), key=lambda x: x[1], reverse=True)
    total = sum(b for _, b in items)

    render_svg(items, total, Path("assets/lang-card.svg"))

if __name__ == "__main__":
    main()
