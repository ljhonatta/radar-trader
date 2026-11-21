"""Narração automática dos vídeos (roda no GitHub Actions, workflow "Narrar vídeo").

Escolhe a notícia mais importante do dia (ou a que for pedida), escreve o roteiro do vídeo com a OpenAI
no mesmo formato da aba Vídeo do painel, grava a narração no ElevenLabs cena a cena (com o tempo de cada
palavra, para a legenda) e salva tudo em docs/data/videos/<id>/. O painel abre esse vídeo pronto: é só gravar.

Chaves (nunca no código): ELEVENLABS_API_KEY e OPENAI_API_KEY vêm do ambiente; no computador, de .env.local.
"""
import base64, json, os, re, sys
from datetime import datetime, timedelta, timezone

import requests
from dotenv import load_dotenv
from elevenlabs import ElevenLabs, VoiceSettings

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(RAIZ, ".env.local"))  # no computador; no GitHub as chaves já vêm do ambiente

BRT = timezone(timedelta(hours=-3))
ARQ_NOTICIAS = os.path.join(RAIZ, "docs", "data", "noticias.json")
PASTA = os.path.join(RAIZ, "docs", "data", "videos")
ARQ_INDICE = os.path.join(PASTA, "index.json")

OPENAI = os.environ.get("OPENAI_API_KEY", "").strip()
MODELO_TEXTO = os.environ.get("OPENAI_MODEL_ESCRITA", "").strip() or "gpt-4.1-mini"
VOZ = os.environ.get("NARRAR_VOZ", "").strip() or "JBFqnCBsd6RMkjVDRZzb"  # George (voz padrão do ElevenLabs)
MODELO_VOZ = os.environ.get("NARRAR_MODELO", "").strip() or "eleven_v4"
PERFIL = os.environ.get("NARRAR_PERFIL", "").strip() or "@traderjhonatta"
POR_DIA = int(os.environ.get("NARRAR_POR_DIA", "").strip() or "1")
NOTICIA_ID = os.environ.get("NOTICIA_ID", "").strip()

OBJETOS = ["seta-baixo", "seta-cima", "termometro", "pilha", "moedas", "predio", "placa-pare", "alvo", "relogio", "calendario", "cartao",
           "escudo", "lupa", "barras", "pessoa", "grupo", "cifrao", "barril", "cofre", "casa", "carrinho", "monitor", "megafone", "balanca"]


def ler(caminho, padrao):
    try:
        with open(caminho, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return padrao


def gravar(caminho, obj):
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)


# ---------------- roteiro (mesmo formato da aba Vídeo) ----------------
def roteiro(n):
    fim = "Segue o perfil pra ficar por dentro das novidades do mercado todo dia!"
    material = {k: n.get(k) for k in ("titulo", "resumo", "explicacao", "fatos", "numeros", "comparativo", "declaracoes",
                                       "porQueImporta", "impactoMercado", "entenda", "observar", "fonte")}
    prompt = f"""Você é roteirista de Reels em português do Brasil. Perfil {PERFIL}: notícias do mercado financeiro explicadas de um jeito simples para quem investe ou quer começar.
NOTÍCIA: {json.dumps(material, ensure_ascii=False)}
Escreva um roteiro de vídeo vertical de 55 a 80 segundos, falado como um criador de conteúdo brasileiro que prende a atenção: energia, curiosidade e ritmo de Reels. Use frases curtas de impacto, perguntas que puxam a próxima cena ("E sabe o que aconteceu depois?"), viradas ("E não parou aí…"), reticências e vírgulas para marcar pausas, expressões naturais do dia a dia. Nada de clichê de coach, sem emoji, sem prometer ganho, sem recomendar compra ou venda. Escreva os números por extenso quando ajudar a leitura em voz alta, mas no campo "valor" use o número curto. Só use números, nomes e fatos do material.
Estrutura: gancho forte; o que aconteceu; os números; por que importa; o que muda para quem assiste; um conceito explicado; o que observar; fechamento: {fim}
Nunca escreva @ nem o nome do perfil nas falas (a voz não lê bem); no fechamento, só convide a seguir o perfil para acompanhar as novidades.
Divida em 9 a 12 cenas de 8 a 24 palavras cada. A maioria das cenas é do tipo "cena", com 3 a 4 elementos que aparecem um a um, cada um na palavra da fala que o menciona.
Formato: {{"tipo":"cena","topico":"faixa no topo, até 6 palavras em caixa alta","continua":false,"atores":[...]}}
Elementos (cada um com "gatilho": a palavra exata da fala em que ele entra):
- {{"tipo":"objeto","objeto":"um dos objetos","rotulo":"etiqueta até 4 palavras","direcao":"sobe|cai","gatilho":""}}
- {{"tipo":"numero","valor":"número curto do material","rotulo":"até 7 palavras","gatilho":""}}
- {{"tipo":"etiqueta","texto":"até 6 palavras","gatilho":""}}
- {{"tipo":"citacao","frase":"paráfrase curta","quem":"nome e cargo do material","gatilho":""}}
Use "continua":true quando a cena seguinte é sobre o mesmo assunto (o palco fica e só ganha elementos novos). Para comparar, use vários objetos lado a lado, cada um com seu rótulo.
A última cena é {{"tipo":"fim","texto":"Seguir"}} com a fala de fechamento.
Objetos possíveis: {", ".join(OBJETOS)}. "pessoa" é um personagem; "grupo" para pessoas em geral.
"cap" é a etiqueta do capítulo em 1 ou 2 palavras (A NOTÍCIA, A CONTA, O IMPACTO, ENTENDA, E AGORA).
"tom" é a direção de voz da cena, uma de: excited, serious, curious, confident, warm.
Responda só com JSON: {{"cenas":[{{"cap":"","narracao":"","tom":"","visual":{{}}}}],"legenda":"legenda do post com 2 parágrafos, a fonte e 5 hashtags"}}"""
    r = requests.post("https://api.openai.com/v1/chat/completions",
                      headers={"Authorization": f"Bearer {OPENAI}", "Content-Type": "application/json"},
                      json={"model": MODELO_TEXTO, "response_format": {"type": "json_object"},
                            "messages": [{"role": "system", "content": "Responda sempre em JSON válido."}, {"role": "user", "content": prompt}]},
                      timeout=180)
    r.raise_for_status()
    d = json.loads(r.json()["choices"][0]["message"]["content"])
    cenas = [c for c in d.get("cenas", []) if str(c.get("narracao", "")).strip()]
    if not cenas or (cenas[-1].get("visual") or {}).get("tipo") != "fim":
        cenas.append({"cap": "", "narracao": fim, "tom": "warm", "visual": {"tipo": "fim", "texto": "Seguir"}})
    return cenas, str(d.get("legenda", ""))


# ---------------- narração ----------------
TONS = {"excited", "serious", "curious", "confident", "warm"}


def narrar_cena(cliente, texto, tom, antes, depois):
    """Grava uma cena e devolve (mp3, duração, início de cada palavra em segundos)."""
    tag = f"[{tom}] " if tom in TONS and MODELO_VOZ in ("eleven_v4", "eleven_v3") else ""
    texto = re.sub(r"@[\w.]+", "o perfil", texto)  # a voz tropeça no @ do perfil
    entrada = tag + texto
    extra = {}
    if MODELO_VOZ != "eleven_multilingual_v2":
        extra["language_code"] = "pt"  # o multilingual_v2 não aceita forçar o idioma
    if antes:
        extra["previous_text"] = antes
    if depois:
        extra["next_text"] = depois
    r = cliente.text_to_speech.convert_with_timestamps(
        voice_id=VOZ, text=entrada, model_id=MODELO_VOZ, output_format="mp3_44100_128",
        voice_settings=VoiceSettings(stability=0.35, similarity_boost=0.8), **extra,
    )
    mp3 = base64.b64decode(r.audio_base_64)
    al = r.alignment or r.normalized_alignment
    ini_c, fim_c = list(al.character_start_times_seconds), list(al.character_end_times_seconds)
    dur = (fim_c[-1] if fim_c else 0) + 0.15
    # início de cada palavra da fala (sem a etiqueta de tom), pela posição dos caracteres
    palavras = texto.split()
    tempos, pos = [], len(tag)
    alinhado = len(al.characters) == len(entrada)
    for w in palavras:
        j = entrada.find(w, pos)
        if alinhado and j >= 0 and j < len(ini_c):
            tempos.append(round(ini_c[j], 3))
            pos = j + len(w)
        else:
            tempos.append(None)
    # palavras que não casaram: distribui pelo tamanho entre as vizinhas
    for k, t in enumerate(tempos):
        if t is None:
            tempos[k] = round(dur * k / max(1, len(palavras)), 3)
    return mp3, round(dur, 3), tempos


def escolher(noticias, feitos):
    if NOTICIA_ID:
        return [n for n in noticias if n.get("id") == NOTICIA_ID]
    hoje = datetime.now(BRT).strftime("%Y-%m-%d")
    ja_hoje = sum(1 for v in feitos.values() if str(v.get("criadoEm", "")).startswith(hoje))
    falta = max(0, POR_DIA - ja_hoje)
    boas = [n for n in noticias if n.get("tipo") != "sinal" and n.get("id") not in feitos and n.get("explicacao")
            and str(n.get("data", "")) >= (datetime.now(BRT) - timedelta(days=1)).strftime("%Y-%m-%d")]
    boas.sort(key=lambda n: (n.get("impacto") != "alto", n.get("ordem", 99), -len(" ".join(n.get("explicacao") or []))))
    return boas[:falta]


def main():
    if not os.environ.get("ELEVENLABS_API_KEY"):
        sys.exit("Falta a chave ELEVENLABS_API_KEY (segredo do repositório no GitHub ou .env.local no computador).")
    if not OPENAI:
        sys.exit("Falta a chave OPENAI_API_KEY.")
    cliente = ElevenLabs()  # o SDK lê ELEVENLABS_API_KEY do ambiente
    noticias = ler(ARQ_NOTICIAS, [])
    indice = ler(ARQ_INDICE, {})
    alvo = escolher(noticias, indice)
    if not alvo:
        print("Nada para narrar agora (cota do dia feita ou nenhuma notícia boa).")
        return
    for n in alvo:
        cenas, legenda = roteiro(n)
        for c in cenas:  # fala e legenda sem @ do perfil
            c["narracao"] = re.sub(r"\s{2,}", " ", re.sub(r"@[\w.]+", "o perfil", str(c.get("narracao", "")))).strip()
        pasta = os.path.join(PASTA, n["id"])
        os.makedirs(pasta, exist_ok=True)
        saida, total = [], 0
        for i, c in enumerate(cenas):
            mp3, dur, tw = narrar_cena(cliente, str(c["narracao"]).strip(), str(c.get("tom", "")).lower(),
                                       cenas[i - 1]["narracao"] if i else "", cenas[i + 1]["narracao"] if i + 1 < len(cenas) else "")
            nome = f"cena-{i + 1:02d}.mp3"
            with open(os.path.join(pasta, nome), "wb") as f:
                f.write(mp3)
            saida.append({"cap": c.get("cap", ""), "narracao": c["narracao"], "visual": c.get("visual") or {}, "audio": nome, "dur": dur, "tw": tw})
            total += len(c["narracao"])
            print(f"  cena {i + 1}: {dur:.1f}s")
        gravar(os.path.join(pasta, "video.json"), {"noticiaId": n["id"], "titulo": n.get("titulo"), "perfil": PERFIL, "voz": VOZ,
                                                    "modelo": MODELO_VOZ, "criadoEm": datetime.now(BRT).replace(microsecond=0).isoformat(),
                                                    "cenas": saida, "legenda": legenda})
        indice[n["id"]] = {"pasta": f"data/videos/{n['id']}/video.json", "criadoEm": datetime.now(BRT).replace(microsecond=0).isoformat(),
                           "titulo": n.get("titulo")}
        print(f"Narrado: {n['titulo']} ({len(saida)} cenas, {total} caracteres)")
    # guarda só os vídeos dos últimos 7 dias
    limite = (datetime.now(BRT) - timedelta(days=7)).isoformat()
    for k in [k for k, v in indice.items() if str(v.get("criadoEm", "")) < limite]:
        indice.pop(k)
        pasta = os.path.join(PASTA, k)
        for f in os.listdir(pasta) if os.path.isdir(pasta) else []:
            os.remove(os.path.join(pasta, f))
        if os.path.isdir(pasta):
            os.rmdir(pasta)
    gravar(ARQ_INDICE, indice)


if __name__ == "__main__":
    main()
