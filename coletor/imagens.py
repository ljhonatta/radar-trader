"""Gera a capa e o ícone do Radar Trader com a OpenAI (roda no GitHub Actions, workflow 'Gerar imagens').
Salva em docs/data/img/ia-capa.png e docs/data/img/ia-icone.png. Para refazer, rode o workflow de novo
(pode mudar os textos em CAPA e ICONE abaixo)."""
import base64, os, sys

import requests

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA = os.path.join(RAIZ, "docs", "data", "img")
API_KEY = os.environ.get("OPENAI_API_KEY", "").strip()

CAPA = ("Wide cinematic hero banner for a Brazilian financial-markets news app called Radar Trader. Dark navy-black "
        "background, glowing orange (#ff6a13) and amber accents. A sleek futuristic trading terminal: a circular radar "
        "sweep blended with rising candlestick charts and thin data lines, subtle grid, soft bokeh city lights of São Paulo "
        "skyline at the bottom. Premium, editorial, high contrast, lots of empty dark space on the left for a title. "
        "No text, no letters, no numbers, no logos, no people.")
ICONE = ("Flat vector app icon, full bleed square, solid dark navy background (#0c1019) edge to edge. One bold solid orange "
         "(#ff6a13) symbol filling about 75% of the canvas: a quarter-circle radar sweep (two thick concentric arcs from a "
         "corner point) with a thick zigzag trading line rising to an arrow head on top. Crisp sharp edges, NO glow, NO blur, "
         "NO gradient, NO shadow, no border, high contrast, perfectly legible at 16x16 pixels. No text, no letters, no numbers.")


def gerar(prompt, tamanho, arquivo):
    erros = []
    for modelo, extra in (("gpt-image-1", {"quality": "high"}), ("dall-e-3", {"quality": "hd", "response_format": "b64_json"})):
        size = tamanho if modelo == "gpt-image-1" else {"1536x1024": "1792x1024"}.get(tamanho, tamanho)
        r = requests.post("https://api.openai.com/v1/images/generations",
                          headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
                          json={"model": modelo, "prompt": prompt, "size": size, "n": 1, **extra}, timeout=300)
        if r.status_code == 200:
            with open(os.path.join(PASTA, arquivo), "wb") as f:
                f.write(base64.b64decode(r.json()["data"][0]["b64_json"]))
            print(f"{arquivo}: gerado com {modelo} ({size})")
            return
        erros.append(f"{modelo} {r.status_code}: {r.text[:200]}")
    raise RuntimeError(" | ".join(erros))


if __name__ == "__main__":
    if not API_KEY:
        sys.exit("Falta o segredo OPENAI_API_KEY.")
    qual = sys.argv[1] if len(sys.argv) > 1 else "ambos"
    if qual in ("ambos", "capa"):
        gerar(CAPA, "1536x1024", "ia-capa.png")
    if qual in ("ambos", "icone"):
        gerar(ICONE, "1024x1024", "ia-icone.png")
