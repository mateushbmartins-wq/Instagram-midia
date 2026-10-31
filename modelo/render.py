"""Gera as lâminas do carrossel (1080x1350) a partir de arquivos .dc.html.

Uso:
    python3 modelo/render.py <pasta-com-os-.dc.html> <pasta-de-saida>

Os arquivos são renderizados em ordem alfabética (use 1.dc.html, 2.dc.html...).
A foto do cabeçalho é assets/avatar.jpg. As fontes Inter vêm de
`npm i @fontsource/inter` instalado em qualquer pasta (caminho em FONTS_DIR).
"""
import os, re, sys, pathlib
from playwright.sync_api import sync_playwright
from PIL import Image

repo = pathlib.Path(__file__).resolve().parent.parent
src_dir = pathlib.Path(sys.argv[1]).resolve()
out_dir = pathlib.Path(sys.argv[2]).resolve()
out_dir.mkdir(parents=True, exist_ok=True)
fonts = pathlib.Path(os.environ.get("FONTS_DIR", "node_modules/@fontsource/inter/files")).resolve()
avatar = (repo / "assets" / "avatar.jpg").as_uri()

faces = ""
for sub in ("latin", "latin-ext"):
    for w in (400, 500, 700, 800):
        f = fonts / f"inter-{sub}-{w}-normal.woff2"
        if f.exists():
            faces += f"@font-face{{font-family:Inter;font-weight:{w};src:url('{f.as_uri()}') format('woff2');}}"

files = sorted(p for p in src_dir.glob("*.dc.html"))
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1080, "height": 1350})
    for i, f in enumerate(files, 1):
        src = f.read_text(encoding="utf-8")
        body = re.search(r"<x-dc>(.*)</x-dc>", src, re.S).group(1)
        body = re.sub(r"<helmet>.*?</helmet>", "", body, flags=re.S)
        body = re.sub(r'src="[^"]*avatar[^"]*"', f'src="{avatar}"', body)
        html = f"<!doctype html><html><head><meta charset='utf-8'><style>{faces}body{{margin:0}}</style></head><body>{body}</body></html>"
        tmp = out_dir / f"_tmp{i}.html"
        tmp.write_text(html, encoding="utf-8")
        pg.goto(tmp.as_uri())
        pg.evaluate("document.fonts.ready")
        pg.wait_for_timeout(300)
        png = out_dir / f"{i}.png"
        pg.screenshot(path=str(png), clip={"x": 0, "y": 0, "width": 1080, "height": 1350})
        Image.open(png).convert("RGB").save(out_dir / f"{i}.jpg", quality=82, optimize=True, progressive=True)
        png.unlink(); tmp.unlink()
        print(out_dir / f"{i}.jpg")
    b.close()
