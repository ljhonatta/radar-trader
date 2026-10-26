"""Coletor do Radar Trader 2.0: roda no GitHub Actions, sem o Claude.

1. Lê os feeds RSS e as buscas do Google Notícias (coletor/fontes.json).
2. Pede à OpenAI para escolher as notícias mais úteis para quem opera ou quer
   começar no mercado e escrever cada uma com fatos, números, por que importa,
   impacto, conceito educativo, o que observar, ganchos e ideias de post.
3. Lê sinais do mercado de previsões (Polymarket), só economia e mercado.
4. Atualiza o painel de cotações (Yahoo Finance, AwesomeAPI e Banco Central).
5. Grava docs/data/noticias.json e docs/data/meta.json, que o painel lê.
"""
import json, os, re, sys, time, unicodedata
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import quote_plus

import feedparser
import requests
from bs4 import BeautifulSoup

BRT = timezone(timedelta(hours=-3))
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARQ_NOTICIAS = os.path.join(RAIZ, "docs", "data", "noticias.json")
ARQ_META = os.path.join(RAIZ, "docs", "data", "meta.json")
ARQ_FONTES = os.path.join(RAIZ, "coletor", "fontes.json")

API_KEY = os.environ.get("OPENAI_API_KEY", "").strip()
MODELO = os.environ.get("OPENAI_MODEL", "").strip() or "gpt-4o-mini"
# modelo que escreve a ficha completa (mais caprichado); se a conta não tiver, cai no MODELO
MODELO_ESCRITA = os.environ.get("OPENAI_MODEL_ESCRITA", "").strip() or "gpt-4.1-mini"
MANUAL = os.environ.get("MANUAL", "false").lower() == "true"
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"}

MAX_NOTICIAS = 22      # por coleta
MAX_ALTO = 5           # destaques por coleta
MAX_SINAIS = 5
MAX_CANDIDATOS = 220
MAX_POR_FONTE = 18
DIAS_GUARDAR = 7

CATEGORIAS = ["Bolsa", "Câmbio", "Juros", "Inflação", "Economia", "Global", "Empresas", "Commodities",
              "Política monetária", "Day trade", "Renda fixa", "Cripto", "FIIs", "Dividendos", "Produtos",
              "Agenda", "Comportamento do investidor"]
PUBLICOS = ["Iniciantes", "Day traders", "Investidores", "Empresários", "CLT", "Aposentados"]
ICONES = ["grafico", "seta", "queda", "moeda", "raio", "escudo", "alvo", "foguete", "globo", "relogio", "cadeado"]
FORMATOS = ["Carrossel", "Reels", "Stories"]

PERFIL = ("Perfil de notícias e educação em mercado financeiro (Trader School Wendell Guimarães: faculdade de "
          "mercado financeiro e day trade na B3). As notícias viram carrosséis educativos de Instagram para quem "
          "opera ou quer começar: o perfil funciona como um portal de notícias do mercado explicadas de um jeito simples.")
REGRAS = ("REGRAS DE OURO: nunca invente notícias, números, cotações, declarações, datas ou fontes. Use SOMENTE o "
          "que está no texto da fonte, com suas palavras (não copie trechos). Explicações educativas gerais sobre como "
          "o mercado funciona são permitidas, sem fatos novos sobre o caso. Nunca prometa ganhos nem recomende comprar "
          "ou vender ativo. Política e eleições: só o efeito no mercado, neutro. Escreva em português do Brasil.")
PROIBIDO_SINAL = re.compile(r"elect|president|senat|congress|governor|trump|biden|harris|lula|bolsonaro|vote|"
                            r"party|primary|war|invade|nba|nfl|fifa|world cup|oscar|grammy|tweet|celebrity|"
                            r"pope|ceasefire|nominee|democrat|republican|mayor|minister|prime", re.I)


def agora():
    return datetime.now(BRT).replace(microsecond=0)


def iso(dt):
    return dt.astimezone(BRT).replace(microsecond=0).isoformat()


def norm(t):
    t = unicodedata.normalize("NFKD", t or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9 ]", " ", re.sub(r"\s+", " ", t)).strip()


def ler_json(caminho, padrao):
    try:
        with open(caminho, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return padrao


def gravar_json(caminho, obj):
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)


def corta(s, n):
    return " ".join(str(s or "").split()[:n])


# ---------------- coleta de notícias ----------------
def data_item(e):
    for k in ("published_parsed", "updated_parsed"):
        v = e.get(k)
        if v:
            return datetime.fromtimestamp(time.mktime(v), tz=timezone.utc)
    for k in ("published", "updated"):
        v = e.get(k)
        if v:
            try:
                return parsedate_to_datetime(v)
            except Exception:
                pass
    return None


def limpar_html(s, n=400):
    return re.sub(r"\s+", " ", BeautifulSoup(s or "", "html.parser").get_text(" ")).strip()[:n]


def ler_feed(url):
    r = requests.get(url, headers=UA, timeout=25)
    r.raise_for_status()
    f = feedparser.parse(r.content)
    if f.bozo and not f.entries:
        raise RuntimeError("feed inválido")
    return f.entries


RUIDO = re.compile(r"loteria|mega-sena|quina|lotofácil|horóscopo|bbb|novela|receita de|futebol", re.I)


def coletar(fontes, inicio, falhas):
    itens = []
    for fonte in fontes["feeds"]:
        entradas = None
        for url in [fonte["url"]] + ([fonte["reserva"]] if fonte.get("reserva") else []):
            try:
                entradas = ler_feed(url)
                break
            except Exception as ex:
                erro = type(ex).__name__
        if entradas is None:
            falhas.append(f"{fonte['nome']} ({erro})")
            continue
        for e in entradas:
            dt = data_item(e)
            if not dt or dt < inicio:
                continue
            titulo = limpar_html(e.get("title"), 220)
            if RUIDO.search(titulo):
                continue
            itens.append({"titulo": titulo, "url": e.get("link", ""), "fonte": fonte["nome"],
                          "resumo": limpar_html(e.get("summary") or e.get("description")),
                          "publicado": dt, "direto": True})
    for q in fontes["buscas"]:
        url = f"https://news.google.com/rss/search?q={quote_plus(q + ' when:1d')}&hl=pt-BR&gl=BR&ceid=BR:pt-419"
        try:
            for e in ler_feed(url)[:12]:
                dt = data_item(e)
                if not dt or dt < inicio:
                    continue
                titulo = limpar_html(e.get("title"), 220)
                veiculo = (e.get("source") or {}).get("title", "")
                if veiculo and titulo.endswith(" - " + veiculo):
                    titulo = titulo[: -len(veiculo) - 3]
                itens.append({"titulo": titulo, "url": "", "gnews": e.get("link", ""), "fonte": veiculo or "Google Notícias",
                              "resumo": "", "publicado": dt, "direto": False})
        except Exception as ex:
            falhas.append(f"Google Notícias '{q}' ({type(ex).__name__})")
    vistos, unicos, por_fonte = set(), [], {}
    for it in sorted(itens, key=lambda i: (not i["direto"], -i["publicado"].timestamp())):
        k = norm(it["titulo"])[:70]
        if not k or k in vistos or (it["url"] and it["url"] in vistos):
            continue
        por_fonte[it["fonte"]] = por_fonte.get(it["fonte"], 0) + 1
        if por_fonte[it["fonte"]] > MAX_POR_FONTE:
            continue
        vistos.add(k)
        if it["url"]:
            vistos.add(it["url"])
        unicos.append(it)
    return unicos[:MAX_CANDIDATOS]


def extrair(html):
    """Pega o corpo da matéria: primeiro o articleBody do JSON-LD, depois o maior bloco de parágrafos."""
    sopa = BeautifulSoup(html, "html.parser")
    cands = []
    for sc in sopa.find_all("script", type="application/ld+json"):
        try:
            d = json.loads(sc.string or "")
            for x in (d if isinstance(d, list) else d.get("@graph", [d])):
                if isinstance(x, dict) and x.get("articleBody"):
                    cands.append(BeautifulSoup(x["articleBody"], "html.parser").get_text(" "))
        except Exception:
            pass
    for t in sopa(["script", "style", "nav", "footer", "header", "aside", "form", "figure"]):
        t.decompose()
    for sel in ["article", "[itemprop=articleBody]", ".article-body", ".entry-content", ".post-content", ".content-text", "main"]:
        for el in sopa.select(sel):
            ps = [p.get_text(" ", strip=True) for p in el.find_all(["p", "li", "h2"])]
            cands.append(" ".join(p for p in ps if len(p) > 30))
    ps = [p.get_text(" ", strip=True) for p in sopa.find_all("p")]
    cands.append(" ".join(p for p in ps if len(p) > 40))
    melhor = max(cands, key=len) if cands else ""
    corta_em = re.search(r"(Leia também|Leia mais|Veja também|Assine|Newsletter|Receba as notícias)", melhor)
    if corta_em and corta_em.start() > 1500:
        melhor = melhor[:corta_em.start()]
    return re.sub(r"\s+", " ", melhor).strip()


def texto_materia(url):
    try:
        r = requests.get(url, headers=UA, timeout=25)
        r.raise_for_status()
        return extrair(r.text)[:12000]
    except Exception:
        return ""


def link_google(gurl):
    """Abre o link do Google Notícias e devolve o endereço real da matéria (ou vazio)."""
    try:
        m = re.search(r"/articles/([^?]+)", gurl or "")
        if not m:
            return ""
        gid = m.group(1)
        h = requests.get(f"https://news.google.com/articles/{gid}", headers=UA, timeout=20).text
        sg = re.search(r'data-n-a-sg="([^"]+)"', h)
        ts = re.search(r'data-n-a-ts="([^"]+)"', h)
        if not (sg and ts):
            return ""
        req = [["Fbv4je", f'["garturlreq",[["X","X",["X","X"],null,null,1,1,"US:en",null,1,null,null,null,null,null,0,1],'
                f'"X","X",1,[1,1,1],1,1,null,0,0,null,0],"{gid}",{ts.group(1)},"{sg.group(1)}"]']]
        r = requests.post("https://news.google.com/_/DotsSplashUi/data/batchexecute",
                          headers={**UA, "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"},
                          data="f.req=" + quote_plus(json.dumps([req])), timeout=20)
        j = json.loads(r.text.split("\n\n")[1])[:-2]
        url = json.loads(j[0][2])[1]
        return url if url.startswith("http") else ""
    except Exception:
        return ""


def preparar(c):
    """Garante link real e texto completo da matéria para a IA escrever com conteúdo de verdade."""
    if not c["direto"] and c.get("gnews"):
        real = link_google(c["gnews"])
        if real:
            c["url"], c["direto"] = real, True
    return texto_materia(c["url"]) if c["direto"] and c["url"] else ""


# ---------------- IA ----------------
ESCRITA_OK = [True]


def ia(sistema, usuario, modelo=None):
    modelo = modelo or MODELO
    for tentativa in range(3):
        r = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
            json={"model": modelo, "response_format": {"type": "json_object"},
                  "messages": [{"role": "system", "content": sistema}, {"role": "user", "content": usuario}]},
            timeout=150,
        )
        if r.status_code == 429 or r.status_code >= 500:
            time.sleep(10 * (tentativa + 1))
            continue
        if r.status_code in (400, 403, 404) and modelo != MODELO and "model" in r.text:
            ESCRITA_OK[0] = False
            return ia(sistema, usuario, MODELO)
        if r.status_code != 200:
            raise RuntimeError(f"OpenAI {r.status_code}: {r.text[:300]}")
        return json.loads(r.json()["choices"][0]["message"]["content"])
    raise RuntimeError("OpenAI sem resposta depois de 3 tentativas")


def triagem(candidatos, recentes):
    lista = "\n".join(f"[{i}] {c['fonte']} | {c['titulo']} | {c['resumo'][:200]}" for i, c in enumerate(candidatos))
    ja = "\n".join(f"{d['id']} | {d['titulo']}" for d in recentes) or "(nenhuma)"
    sistema = (f"Você é o editor-chefe do 'Radar Trader'. {PERFIL}\n{REGRAS}\n"
               f"Temas aceitos: {', '.join(CATEGORIAS)}. Descarte fofoca corporativa sem impacto, loterias, lifestyle, "
               "finanças pessoais genéricas, entretenimento e streaming (séries, filmes, celebridades) e matérias patrocinadas (Blue Studio, publieditorial). Priorize o que mexe com bolsa, dólar, juros, "
               "inflação e grandes empresas e o que ajuda a educar quem opera. Responda em JSON.")
    usuario = (f"Notícias candidatas:\n{lista}\n\nNotícias já gravadas nos últimos dias (não repita a mesma história):\n{ja}\n\n"
               "ANTES de escolher, agrupe as candidatas por HISTÓRIA: matérias de veículos diferentes sobre o mesmo "
               "acontecimento e a mesma causa no mesmo dia são UMA história (ex.: 'dólar dispara', 'Bolsa aciona circuit "
               "breaker' e 'Ibovespa futuro despenca' pela mesma razão). Só separe quando o fato principal for outro "
               "(ex.: 'Tesouro cancela leilões' é outra história). "
               'Devolva {"escolhidas":[{"i":<número da candidata principal, a mais completa e confiável>,'
               '"extras":[<até 2 números de OUTRAS candidatas da MESMA história, de outros veículos, para completar a ficha>],'
               '"impacto":"alto|medio","ordem":<1 = melhor para conteúdo>,'
               '"atualiza":"<id da notícia já gravada se for a MESMA história com FATO NOVO, senão null>"}]}. '
               f"No máximo {MAX_NOTICIAS} histórias e no máximo {MAX_ALTO} com impacto alto. Mesma história já gravada "
               "sem fato novo: não inclua. Lista vazia se nada servir.")
    r = ia(sistema, usuario)
    saida, vistos = [], set()
    for e in r.get("escolhidas", []):
        try:
            i = int(e["i"])
        except Exception:
            continue
        if 0 <= i < len(candidatos) and i not in vistos:
            vistos.add(i)
            extras = []
            for j in (e.get("extras") or [])[:2]:
                try:
                    j = int(j)
                except Exception:
                    continue
                if 0 <= j < len(candidatos) and j != i and j not in vistos:
                    vistos.add(j)
                    extras.append(candidatos[j])
            saida.append({"c": candidatos[i], "extras": extras, "impacto": "alto" if e.get("impacto") == "alto" else "medio",
                          "ordem": int(e.get("ordem") or 99), "atualiza": e.get("atualiza") or None})
    saida.sort(key=lambda x: (x["impacto"] != "alto", x["ordem"]))
    altos = 0
    for s in saida:
        if s["impacto"] == "alto":
            altos += 1
            if altos > MAX_ALTO:
                s["impacto"] = "medio"
    return saida[:MAX_NOTICIAS]


MODELO_DOC = {
    "titulo": "até 14 palavras, jornalístico, com o fato principal", "resumo": "2 frases, até 45 palavras, com o principal número ou nome",
    "explicacao": ["3 a 4 parágrafos curtos (cada um 30 a 55 palavras) explicando a notícia de forma didática, na ordem: o que aconteceu "
                   "(com números, nomes e datas da matéria); por que aconteceu (causas citadas na matéria); o que isso significa; "
                   "o que vem agora. Use os detalhes concretos da matéria, nada genérico"],
    "fatos": ["5 a 10 frases curtas, cada uma com um fato concreto da matéria (número, nome, data, valor, percentual)"],
    "detalhes": ["4 a 7 pontos de detalhe da matéria que um leitor curioso quer saber: quem, quanto, quando, onde, como, comparação com antes, contexto citado"],
    "declaracoes": [{"quem": "nome e cargo de quem falou, como está na matéria", "oque": "paráfrase curta (até 25 palavras) do que disse"}],
    "cronologia": [{"quando": "data ou momento citado", "oque": "o que aconteceu, até 15 palavras"}],
    "numeros": [{"valor": "só números da fonte, curto, ex: 205.079 ou +7% ou R$ 5,05", "rotulo": "até 10 palavras explicando o número"}],
    "comparativo": [{"item": "ex: Selic", "antes": "valor anterior da fonte", "depois": "valor novo da fonte"}],
    "destaque": "o número principal, curto, ou vazio",
    "porQueImporta": "45 a 65 palavras: por que isso importa para quem investe ou opera, ligando aos fatos da matéria",
    "impactoMercado": "45 a 65 palavras: o que pode mudar para o mercado e para o investidor (setores, ativos, juros, dólar citados), sem prever preço",
    "entenda": "45 a 65 palavras: explique para iniciante o conceito central da notícia (ex: o que é o Ibovespa, juros futuros, recuperação judicial, circuit breaker)",
    "glossario": [{"termo": "termo técnico da matéria", "significado": "até 20 palavras, simples"}],
    "observar": "35 a 55 palavras: próximos eventos, datas e dados citados para acompanhar, em linguagem condicional",
    "pergunta": "pergunta curta para engajar os seguidores nos comentários, ligada à notícia",
    "publico": ["da lista"],
    "angulo": "até 40 palavras: como a notícia vira conteúdo que leva a pessoa a querer entender o mercado e conhecer a faculdade, sem prometer ganhos",
    "gancho": "título de capa até 9 palavras com 1 a 3 palavras-chave entre *asteriscos*",
    "ideias": ["3 títulos curtos de posts diferentes sobre a notícia"],
    "formatos": ["entre Carrossel, Reels, Stories"],
    "categoria": "uma da lista", "icone": "um de: " + ", ".join(ICONES),
    "fonte": "nome do veículo", "data_publicacao": "AAAA-MM-DD se o texto informar, senão null",
    "suficiente": "true se o texto tem fatos suficientes; false se não dá para escrever sem inventar",
}


def escrever(c, texto):
    sistema = (f"Você é um jornalista de mercado financeiro que escreve fichas completas de notícia para virar carrossel "
               f"educativo de Instagram. {PERFIL}\n{REGRAS}\n"
               "Seja ESPECÍFICO e COMPLETO: aproveite ao máximo o texto da matéria (nomes, cargos, empresas, valores, "
               "percentuais, datas, causas, comparações, próximos passos). Nada de frase genérica que serviria para "
               "qualquer notícia. Se o texto for curto, escreva menos, mas nunca invente.\n"
               f"Categorias permitidas: {', '.join(CATEGORIAS)}. Públicos permitidos: {', '.join(PUBLICOS)}. "
               "Os campos 'numeros', 'comparativo', 'destaque', 'declaracoes' e 'cronologia' só levam o que está no texto; "
               "deixe a lista vazia se não houver (comparativo só quando o texto traz o valor anterior e o novo). "
               "Responda em JSON exatamente com estas chaves: " + json.dumps(MODELO_DOC, ensure_ascii=False))
    usuario = (f"Veículo: {c['fonte']}\nTítulo: {c['titulo']}\nResumo do feed: {c['resumo']}\n"
               f"Texto da matéria (pode trazer outras coberturas da mesma história; junte as informações, sem repetir): "
               f"{texto or '(indisponível: use só o título e o resumo, com no máximo 3 fatos e sem números que não estejam neles)'}")
    return ia(sistema, usuario, MODELO_ESCRITA)


def deduplicar(novos, recentes):
    """Última checagem: tira da lista nova o que repete uma história já gravada ou outra nova (mesmo fato, outro veículo)."""
    if not novos:
        return novos
    lista = "\n".join(f"[{i}] {d['titulo']} | {d.get('resumo', '')[:160]}" for i, d in enumerate(novos))
    ja = "\n".join(f"- {d['titulo']}" for d in recentes) or "(nenhuma)"
    try:
        r = ia(f"Você é editor e elimina notícias repetidas. {REGRAS} Responda em JSON.",
               f"Notícias NOVAS:\n{lista}\n\nJá publicadas nos últimos dias:\n{ja}\n\n"
               "Uma notícia nova é REPETIDA quando conta o mesmo fato principal de uma já publicada ou de outra nova anterior "
               "na lista (mesmo acontecimento, mesma causa, mesmos números principais), mesmo que o título seja diferente. "
               "Não é repetida quando traz um fato principal diferente (outra empresa, outro número central, outra decisão). "
               "Também marque como repetida o que não tem relação com mercado financeiro e economia. "
               'Devolva {"repetidas":[números das novas a descartar]}.')
        tirar = {int(i) for i in r.get("repetidas", []) if str(i).lstrip("-").isdigit()}
    except Exception as ex:
        print("deduplicar falhou:", ex)
        return novos
    print("repetidas descartadas:", [novos[i]["titulo"] for i in sorted(tirar) if 0 <= i < len(novos)])
    return [d for i, d in enumerate(novos) if i not in tirar]


def atualizar(doc, c, texto):
    sistema = (f"Você atualiza uma ficha de notícia existente com um fato novo. {REGRAS} Responda em JSON com as chaves "
               '"titulo" (até 14 palavras), "resumo" (até 35 palavras), "fatos" (3 a 6 frases, mantendo os antigos que '
               'seguem válidos e incluindo o novo), "numeros" ([{"valor","rotulo"}] só da fonte), '
               '"novo" (true se há de fato um fato novo, senão false).')
    usuario = (f"Ficha atual: {json.dumps({k: doc.get(k) for k in ('titulo', 'resumo', 'fatos', 'numeros')}, ensure_ascii=False)}\n\n"
               f"Nova matéria ({c['fonte']}): {c['titulo']}\n{texto or c['resumo']}")
    return ia(sistema, usuario)


def lista_str(v, n):
    return [str(x).strip() for x in (v or []) if str(x).strip()][:n]


def validar(d, esc, coleta):
    c = esc["c"]
    if not d or d.get("suficiente") is False:
        return None
    fatos = lista_str(d.get("fatos"), 10)
    if len(fatos) < 2:
        return None
    fonte = c["fonte"] if c["direto"] else (c["fonte"] or d.get("fonte") or "")
    doc = {
        "titulo": corta(d.get("titulo") or c["titulo"], 16), "resumo": corta(d.get("resumo"), 50), "fatos": fatos,
        "explicacao": [corta(x, 70) for x in lista_str(d.get("explicacao"), 4)],
        "detalhes": [corta(x, 35) for x in lista_str(d.get("detalhes"), 7)],
        "declaracoes": [{"quem": corta(x.get("quem"), 10), "oque": corta(x.get("oque"), 30)}
                        for x in (d.get("declaracoes") or []) if isinstance(x, dict) and x.get("quem") and x.get("oque")][:3],
        "cronologia": [{"quando": corta(x.get("quando"), 6), "oque": corta(x.get("oque"), 18)}
                       for x in (d.get("cronologia") or []) if isinstance(x, dict) and x.get("quando") and x.get("oque")][:5],
        "glossario": [{"termo": corta(x.get("termo"), 5), "significado": corta(x.get("significado"), 24)}
                      for x in (d.get("glossario") or []) if isinstance(x, dict) and x.get("termo") and x.get("significado")][:3],
        "pergunta": corta(d.get("pergunta"), 20), "tamanhoTexto": esc.get("tam", 0),
        "numeros": [{"valor": str(n.get("valor", "")), "rotulo": str(n.get("rotulo", ""))}
                    for n in (d.get("numeros") or []) if isinstance(n, dict) and n.get("valor")][:6],
        "comparativo": [{"item": str(n.get("item", "")), "antes": str(n.get("antes", "")), "depois": str(n.get("depois", ""))}
                        for n in (d.get("comparativo") or []) if isinstance(n, dict) and n.get("antes") and n.get("depois")][:4],
        "destaque": corta(d.get("destaque"), 3),
        "porQueImporta": corta(d.get("porQueImporta"), 70), "impactoMercado": corta(d.get("impactoMercado"), 70),
        "entenda": corta(d.get("entenda"), 70), "observar": corta(d.get("observar"), 60),
        "publico": [p for p in (d.get("publico") or []) if p in PUBLICOS] or ["Investidores"],
        "angulo": corta(d.get("angulo"), 40), "gancho": corta(d.get("gancho"), 10),
        "ideias": lista_str(d.get("ideias"), 3),
        "formatos": [f for f in (d.get("formatos") or []) if f in FORMATOS] or ["Carrossel"],
        "categoria": d.get("categoria") if d.get("categoria") in CATEGORIAS else "Economia",
        "icone": d.get("icone") if d.get("icone") in ICONES else "grafico",
        "fonte": fonte + "".join(f"; {f}" for f in esc.get("fontesExtras", []) if f != fonte), "impacto": esc["impacto"], "ordem": esc["ordem"],
        "status": "nova", "coletadoEm": iso(coleta),
    }
    if c["direto"] and c["url"]:
        doc["url"] = c["url"]
    else:
        doc["url"] = "https://www.google.com/search?q=" + quote_plus(f"{c['titulo']} {fonte}")
        doc["urlBusca"] = True
    pub = c["publicado"].astimezone(BRT)
    doc["publicadoEm"] = iso(pub)
    doc["data"] = pub.strftime("%Y-%m-%d")
    return doc


# ---------------- mercado de previsões ----------------
def pct(x):
    try:
        return round(float(x) * 100, 1)
    except Exception:
        return None


def probs_evento(ev):
    mk = [m for m in ev.get("markets") or [] if not m.get("closed")]
    out = []
    if len(mk) > 1:
        for m in mk:
            try:
                p = pct(json.loads(m.get("outcomePrices") or "[]")[0])
            except Exception:
                p = None
            if p is not None:
                out.append({"opcao": m.get("groupItemTitle") or m.get("question", ""), "prob": p})
    elif mk:
        try:
            nomes = json.loads(mk[0].get("outcomes") or "[]")
            precos = json.loads(mk[0].get("outcomePrices") or "[]")
            out = [{"opcao": n, "prob": pct(p)} for n, p in zip(nomes, precos) if pct(p) is not None]
        except Exception:
            pass
    out.sort(key=lambda x: -x["prob"])
    return out[:4]


def sinais(fontes, existentes, coleta, falhas):
    eventos, vistos = [], set()
    for url in fontes.get("polymarket", []):
        try:
            r = requests.get(url, headers=UA, timeout=25)
            r.raise_for_status()
            for ev in r.json():
                if ev.get("slug") in vistos:
                    continue
                vistos.add(ev.get("slug"))
                fim = ev.get("endDate") or ""
                if not fim or fim[:10] <= coleta.strftime("%Y-%m-%d"):
                    continue
                if PROIBIDO_SINAL.search(ev.get("title", "") + " " + ev.get("slug", "")):
                    continue
                pr = probs_evento(ev)
                if not pr or pr[0]["prob"] >= 99.5 or pr[0]["prob"] <= 0.5:
                    continue
                eventos.append({"slug": ev["slug"], "titulo": ev.get("title", ""), "prazo": fim[:10],
                                "volume24h": float(ev.get("volume24hr") or 0), "probs": pr})
        except Exception as ex:
            falhas.append(f"Polymarket ({type(ex).__name__})")
    if not eventos:
        return [], 0
    eventos.sort(key=lambda e: -e["volume24h"])
    eventos = eventos[:15]
    sistema = (f"Você escolhe sinais do mercado de previsões (Polymarket) para um perfil de mercado financeiro. {REGRAS}\n"
               "Use SÓ eventos de juros (Fed, Copom), inflação, recessão, câmbio, commodities, petróleo, cripto, grandes "
               "empresas e índices. PROIBIDO: eleições, política, guerras, esportes, entretenimento. Responda em JSON.")
    usuario = (f"Eventos: {json.dumps(eventos, ensure_ascii=False)}\n\n"
               f'Escolha até {MAX_SINAIS} e devolva {{"sinais":[{{"slug":"...","titulo":"Mercado de previsões vê X% de '
               'chance de ... (português, com a probabilidade principal)","resumo":"até 35 palavras, deixando claro que é '
               'probabilidade precificada por apostadores, não previsão oficial","opcoes":["tradução curta de cada opção, '
               'na mesma ordem de probs"],"gancho":"até 7 palavras com 1 a 2 palavras entre *asteriscos*",'
               '"entenda":"até 35 palavras explicando o tema para iniciante","categoria":"Juros|Inflação|Global|Cripto|'
               'Commodities|Câmbio|Empresas"}]}')
    r = ia(sistema, usuario)
    por_slug = {e["slug"]: e for e in eventos}
    ja = {n.get("slug"): n for n in existentes if n.get("tipo") == "sinal"}
    novos, atualizados = [], 0
    for s in r.get("sinais", [])[:MAX_SINAIS]:
        ev = por_slug.get(s.get("slug"))
        if not ev:
            continue
        opcoes = s.get("opcoes") or []
        probs = [{"opcao": str(opcoes[i]) if i < len(opcoes) and opcoes[i] else p["opcao"], "prob": p["prob"]}
                 for i, p in enumerate(ev["probs"])]
        vol = ev["volume24h"]
        doc = {"tipo": "sinal", "slug": ev["slug"], "titulo": corta(s.get("titulo") or ev["titulo"], 18),
               "resumo": corta(s.get("resumo"), 40), "probs": probs, "prazo": ev["prazo"],
               "volume24h": f"US$ {vol / 1e6:.1f} mi".replace(".", ",") if vol >= 1e6 else f"US$ {vol / 1e3:.0f} mil",
               "fatos": [f"{p['opcao']}: {str(p['prob']).replace('.', ',')}%" for p in probs],
               "numeros": [{"valor": f"{str(p['prob']).replace('.', ',')}%", "rotulo": p["opcao"]} for p in probs],
               "destaque": f"{str(probs[0]['prob']).replace('.', ',')}%", "gancho": corta(s.get("gancho"), 8),
               "entenda": corta(s.get("entenda"), 40),
               "categoria": "Previsões", "icone": "alvo", "impacto": "medio", "ordem": 50,
               "fonte": "Polymarket (mercado de previsões)", "url": f"https://polymarket.com/event/{ev['slug']}",
               "publicadoEm": iso(coleta), "horaEstimada": True, "coletadoEm": iso(coleta),
               "data": coleta.strftime("%Y-%m-%d"), "status": "nova"}
        antigo = ja.get(ev["slug"])
        if antigo:
            p0 = (antigo.get("probs") or [{}])[0].get("prob", 0)
            if abs(float(p0 or 0) - probs[0]["prob"]) >= 5:
                antigo.update({k: doc[k] for k in ("titulo", "resumo", "probs", "fatos", "numeros", "destaque", "volume24h")})
                antigo.update({"status": "atualizada", "atualizadoEm": iso(coleta)})
                atualizados += 1
            continue
        novos.append(doc)
    return novos, atualizados


# ---------------- painel de cotações ----------------
def br(v, casas=2):
    s = f"{v:,.{casas}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def var_pct(atual, ant):
    if not ant:
        return ""
    v = (atual / ant - 1) * 100
    return ("+" if v >= 0 else "") + br(v, 2) + "%"


def yahoo(simbolo):
    for host in ("query1", "query2"):
        try:
            r = requests.get(f"https://{host}.finance.yahoo.com/v8/finance/chart/{quote_plus(simbolo)}?range=5d&interval=1d",
                             headers=UA, timeout=20)
            r.raise_for_status()
            m = r.json()["chart"]["result"][0]["meta"]
            p, ant = m.get("regularMarketPrice"), m.get("chartPreviousClose") or m.get("previousClose")
            if p:
                return float(p), float(ant) if ant else None, m.get("regularMarketTime")
        except Exception:
            continue
    return None


def google(cod):
    """Reserva quando o Yahoo bloqueia: lê o preço e o fechamento anterior da página do Google Finance."""
    try:
        t = requests.get(f"https://www.google.com/finance/quote/{cod}", headers=UA, timeout=20).text
        if ":" in cod:  # índices e futuros, ex.: IBOV:INDEXBVMF
            a, b = cod.split(":")
            ini = rf'\["{re.escape(a)}","{re.escape(b)}"\],"[^"]*"'
        else:  # moedas, ex.: USD-BRL
            a, b = cod.split("-")
            ini = rf'"{re.escape(a)} / {re.escape(b)}"'
        m = re.search(ini + r',\d+,(?:null|"[A-Z]+"),\[(-?[\d.E-]+),(-?[\d.E-]+),(-?[\d.E-]+)[^\]]*\],null,(-?[\d.E-]+)(?:,null)*,\[(\d+)\]', t)
        if m:
            return float(m.group(1)), float(m.group(4)), int(m.group(5))
    except Exception:
        pass
    return None


def sgs(serie):
    r = requests.get(f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{serie}/dados/ultimos/1?formato=json", headers=UA, timeout=20)
    r.raise_for_status()
    return float(r.json()[-1]["valor"])


def placar(coleta, antigo, falhas):
    itens, faltou = [], []
    ATIVOS = [("IBOV", "Ibovespa", "^BVSP", "IBOV:INDEXBVMF", lambda v: br(v, 0)), ("USD", "Dólar comercial", "BRL=X", "USD-BRL", lambda v: "R$ " + br(v, 2)),
              ("EUR", "Euro", "EURBRL=X", "EUR-BRL", lambda v: "R$ " + br(v, 2)), ("BTC", "Bitcoin", "BTC-USD", "BTC-USD", lambda v: "US$ " + br(v / 1000, 1) + " mil"),
              ("SPX", "S&P 500", "^GSPC", ".INX:INDEXSP", lambda v: br(v, 0)), ("NDX", "Nasdaq 100", "^NDX", "NDX:INDEXNASDAQ", lambda v: br(v, 0)),
              ("BRENT", "Petróleo Brent", "BZ=F", "BZW00:NYMEX", lambda v: "US$ " + br(v, 2)), ("OURO", "Ouro", "GC=F", "GCW00:COMEX", lambda v: "US$ " + br(v, 2))]
    awesome = {}
    try:
        r = requests.get("https://economia.awesomeapi.com.br/json/last/USD-BRL,EUR-BRL,BTC-USD", headers=UA, timeout=20)
        r.raise_for_status()
        awesome = r.json()
    except Exception:
        pass
    ultimo_pregao = None
    for k, nome, sim, gcod, fmt in ATIVOS:
        moeda = {"USD": "USDBRL", "EUR": "EURBRL", "BTC": "BTCUSD"}.get(k)
        # moedas: a AwesomeAPI traz a variação do dia certa; o Google fica de última reserva
        y = yahoo(sim) or (None if moeda and moeda in awesome else google(gcod))
        if y:
            v, ant, ts = y
            # o Google não traz o fechamento anterior das moedas (vem igual ao preço): sem variação em vez de um falso 0,00%
            semvar = moeda and ant and abs(v / ant - 1) < 5e-5
            itens.append({"k": k, "nome": nome, "v": fmt(v), "var": "" if semvar else var_pct(v, ant)})
            if k == "IBOV" and ts:
                ultimo_pregao = datetime.fromtimestamp(ts, tz=BRT)
            continue
        a = awesome.get({"USD": "USDBRL", "EUR": "EURBRL", "BTC": "BTCUSD"}.get(k, "-"))
        if not a and k == "BTC":
            try:
                cg = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_change=true",
                                  headers=UA, timeout=20).json()["bitcoin"]
                a = {"bid": cg["usd"], "pctChange": cg.get("usd_24h_change") or 0}
            except Exception:
                pass
        if a:
            v = float(a["bid"])
            pc = float(a.get("pctChange") or 0)
            itens.append({"k": k, "nome": nome, "v": fmt(v), "var": ("+" if pc >= 0 else "") + br(pc, 2) + "%"})
        else:
            faltou.append(nome)
    for k, nome, serie in (("SELIC", "Selic meta", 432), ("IPCA", "IPCA 12 meses", 13522)):
        try:
            itens.append({"k": k, "nome": nome, "v": br(sgs(serie), 2) + "%", "var": ""})
        except Exception:
            faltou.append(nome)
    if faltou:
        falhas.append("Sem cotação confiável: " + ", ".join(faltou))
    if not itens:
        return antigo
    hora = coleta.hour + coleta.minute / 60
    util = coleta.weekday() < 5
    pregao_hoje = ultimo_pregao and ultimo_pregao.date() == coleta.date()
    obs = "Parcial do pregão" if util and pregao_hoje and 10 <= hora < 17.5 else "Fechamento" if pregao_hoje else "Último fechamento"
    dias = ["seg", "ter", "qua", "qui", "sex", "sáb", "dom"]
    g = {i["k"]: i for i in itens}
    return {"itens": itens, "obs": obs, "hora": f"{dias[coleta.weekday()]} {coleta.hour}h", "data": coleta.strftime("%Y-%m-%d"),
            "atualizadoEm": iso(coleta), "ibov": g.get("IBOV", {}).get("v", ""), "ibovVar": g.get("IBOV", {}).get("var", ""),
            "dolar": g.get("USD", {}).get("v", ""), "dolarVar": g.get("USD", {}).get("var", ""), "btc": g.get("BTC", {}).get("v", "")}


# ---------------- principal ----------------
def main():
    coleta = agora()
    hoje = coleta.strftime("%Y-%m-%d")
    noticias = ler_json(ARQ_NOTICIAS, [])
    meta = ler_json(ARQ_META, {})
    fontes = ler_json(ARQ_FONTES, {})
    m = meta.get("coleta", {})
    falhas, novas, atualizadas, status, msg, completos = [], 0, 0, "ok", "", 0

    try:
        meta["placar"] = placar(coleta, meta.get("placar"), falhas)
    except Exception as ex:
        falhas.append(f"Painel de cotações ({type(ex).__name__})")

    try:
        if not API_KEY:
            raise RuntimeError("Falta o segredo OPENAI_API_KEY no repositório (Settings → Secrets and variables → Actions).")
        inicio = coleta - timedelta(hours=24)
        if m.get("ultimaColeta"):
            try:
                inicio = min(inicio, datetime.fromisoformat(m["ultimaColeta"]))
            except Exception:
                pass
        inicio = max(inicio, coleta - timedelta(days=3))
        urls = {n.get("url") for n in noticias}
        titulos = {norm(n.get("titulo", ""))[:60] for n in noticias}
        cand = [c for c in coletar(fontes, inicio, falhas) if c["url"] not in urls and norm(c["titulo"])[:60] not in titulos]
        recentes = sorted([n for n in noticias if n.get("tipo") != "sinal"], key=lambda n: n["id"], reverse=True)[:60]
        print(f"{len(cand)} candidatas desde {iso(inicio)}")
        escolhidas = triagem(cand, recentes) if cand else []
        ids = {n["id"]: n for n in noticias}
        nn = max([int(n["id"].rsplit("-", 1)[1]) for n in noticias if re.fullmatch(rf"{hoje}-\d+", n["id"])] or [0])
        textos = {}
        with ThreadPoolExecutor(6) as ex:
            def juntar(e):
                """Texto da matéria principal + até 2 de outros veículos sobre a mesma história."""
                partes = [preparar(e["c"])]
                for x in e.get("extras", []):
                    t = preparar(x)
                    if len(t) > 500:
                        partes.append(f"\n\n[Outra cobertura: {x['fonte']}] " + t[:6000])
                        e.setdefault("fontesExtras", []).append(x["fonte"])
                return "".join(partes)
            for esc, txt in zip(escolhidas, ex.map(juntar, escolhidas)):
                textos[id(esc)] = txt
                esc["tam"] = len(txt)
        completos = sum(1 for e in escolhidas if e.get("tam", 0) > 800)
        print("textos completos:", completos, "de", len(escolhidas))

        def trabalhar(esc):
            txt = textos.get(id(esc), "")
            alvo = ids.get(esc["atualiza"]) if esc["atualiza"] else None
            try:
                if alvo:
                    return ("upd", esc, alvo, atualizar(alvo, esc["c"], txt))
                return ("novo", esc, None, validar(escrever(esc["c"], txt), esc, coleta))
            except Exception as e:
                print(f"falhou '{esc['c']['titulo']}': {e}")
                return ("erro", esc, None, None)

        with ThreadPoolExecutor(4) as ex:
            resultados = list(ex.map(trabalhar, escolhidas))
        destaques = []
        prontos = deduplicar([r for tipo, esc, alvo, r in resultados if tipo == "novo" and r],
                             [n for n in noticias if n.get("tipo") != "sinal" and n.get("coletadoEm", "") >= iso(coleta - timedelta(days=2))])
        ok_ids = {id(x) for x in prontos}
        for tipo, esc, alvo, r in resultados:
            if tipo == "novo" and r and id(r) not in ok_ids:
                continue
            if tipo == "upd" and r and r.get("novo") and r.get("fatos"):
                alvo["fatos"] = lista_str(r["fatos"], 6)
                alvo["titulo"] = corta(r.get("titulo") or alvo["titulo"], 16)
                alvo["resumo"] = corta(r.get("resumo") or alvo.get("resumo"), 40)
                if r.get("numeros"):
                    alvo["numeros"] = [{"valor": str(n.get("valor", "")), "rotulo": str(n.get("rotulo", ""))}
                                       for n in r["numeros"] if isinstance(n, dict) and n.get("valor")][:5]
                if esc["c"]["fonte"] not in alvo.get("fonte", ""):
                    alvo["fonte"] = f"{alvo.get('fonte', '')}; {esc['c']['fonte']}".strip("; ")
                alvo.update({"atualizadoEm": iso(coleta), "status": "atualizada"})
                atualizadas += 1
            elif tipo == "novo" and r:
                nn += 1
                r["id"] = f"{hoje}-{nn:02d}"
                noticias.append(r)
                novas += 1
                destaques.append(r.get("gancho") or r["titulo"])

        try:
            sn, su = sinais(fontes, noticias, coleta, falhas)
            pn = max([int(n["id"].rsplit("-p", 1)[1]) for n in noticias if n["id"].startswith(f"{hoje}-p")] or [0])
            for s in sn:
                pn += 1
                s["id"] = f"{hoje}-p{pn}"
                noticias.append(s)
            novas += len(sn)
            atualizadas += su
        except Exception as ex:
            falhas.append(f"Polymarket ({str(ex)[:80]})")

        if novas or atualizadas:
            msg = f"{novas} nova(s)" + (f" e {atualizadas} atualizada(s)" if atualizadas else "")
            if destaques:
                msg += ": " + "; ".join(d.replace("*", "") for d in destaques[:3]) + "."
        else:
            status = "sem_novas"
            ant = m.get("ultimaColeta")
            quando = datetime.fromisoformat(ant).strftime("%d/%m às %H:%M") if ant else "a última coleta"
            msg = f"Nenhuma notícia nova relevante desde {quando}."
    except Exception as ex:
        status, msg = "erro", str(ex)[:300]
        print(f"ERRO: {ex}")

    hist = [iso(coleta)] + [h for h in m.get("historico", []) if h != iso(coleta)]
    meta["coleta"] = {"ultimaColeta": iso(coleta), "novas": novas, "atualizadas": atualizadas, "status": status,
                      "mensagem": msg, "falhas": falhas[:15], "manual": MANUAL, "historico": hist[:12], "modelo": MODELO,
                      "modeloEscrita": MODELO_ESCRITA if ESCRITA_OK[0] else MODELO, "textosCompletos": completos}
    print(f"{status}: {msg}")
    limite = (coleta - timedelta(days=DIAS_GUARDAR)).strftime("%Y-%m-%d")
    noticias = [n for n in noticias if str(n.get("data", hoje)) >= limite
                and not (n.get("tipo") == "sinal" and str(n.get("prazo", "9999")) < hoje)]
    noticias.sort(key=lambda n: n.get("coletadoEm", ""), reverse=True)
    gravar_json(ARQ_NOTICIAS, noticias)
    gravar_json(ARQ_META, meta)
    if status == "erro":
        sys.exit(1)


if __name__ == "__main__":
    main()
