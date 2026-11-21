"""Copia docs/video.js para o Radar de Pautas e põe a versão no endereço do script nos dois painéis
(assim o celular não fica preso numa versão antiga guardada em cache). Rode depois de mexer no video.js:
    python3 fonte/publicar_video.py && python3 fonte/montar.py"""
import hashlib, os, re, shutil

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIDEO = os.path.join(RAIZ, "docs", "video.js")
PAUTAS = os.path.expanduser("~/Desktop/radar-pautas/docs")
versao = hashlib.sha1(open(VIDEO, "rb").read()).hexdigest()[:10]
shutil.copy(VIDEO, os.path.join(PAUTAS, "video.js"))
for p in (os.path.join(RAIZ, "docs", "index.html"), os.path.join(PAUTAS, "index.html")):
    s = open(p, encoding="utf-8").read()
    s2 = re.sub(r'<script src="video\.js(\?v=[0-9a-f]+)?"></script>', f'<script src="video.js?v={versao}"></script>', s)
    open(p, "w", encoding="utf-8").write(s2)
print("video.js versão", versao)
