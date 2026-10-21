# Radar Trader 2.0

Fábrica de conteúdo financeiro: coleta as notícias do mercado 3 vezes por dia, escreve uma ficha completa de cada uma com IA (OpenAI) e transforma em carrossel de Instagram pronto para baixar. Roda sozinho no GitHub, sem gastar créditos do Claude.

- **Painel:** https://ljhonatta.github.io/radar-trader/
- **Coleta:** todo dia às 6h45, 12h45 e 18h45 (Brasília), pelo GitHub Actions (`.github/workflows/coleta.yml`).

## O que tem de novo na 2.0

- Ficha completa de cada notícia: fatos, números, antes × depois, por que importa, impacto no mercado, conceito "Entenda", o que observar, ângulo para o perfil, 3 ideias de post, público e formato.
- Painel de cotações completo: Ibovespa, dólar, euro, bitcoin, S&P 500, Nasdaq, Brent, ouro, Selic e IPCA.
- Sinais do mercado de previsões (Polymarket): juros, inflação, cripto. Nada de política.
- Carrossel de 3 a 10 slides, com novos slides "Antes × depois" e "Passo a passo".
- Novos modelos: **Terminal** (faixa de cotações + número gigante + ícones 3D) e **Painel 3D**.
- Sem chave de IA no navegador, o carrossel já sai montado com os dados da ficha. Com a chave, a IA reescreve, regenera slides e lê as imagens que você envia.
- Busca nas notícias e "Salvar no celular" com a tela de compartilhar.

## Configuração (uma vez)

1. **Chave da OpenAI no GitHub:** Settings → Secrets and variables → Actions → New repository secret. Nome `OPENAI_API_KEY`, valor a sua chave (começa com `sk-`).
2. **Chave no painel (opcional):** aba Marca → Inteligência artificial. Fica só no navegador.
3. **Testar agora:** Actions → Coleta Radar Trader → Run workflow.

## No dia a dia

- **Atualizar fora do horário:** botão "Atualizar agora" no painel (abre o GitHub; clique em Run workflow).
- **Fontes e buscas:** `coletor/fontes.json`.
- **Modelo da IA na coleta:** padrão `gpt-4o-mini`. Para trocar, crie a variável `OPENAI_MODEL` em Settings → Secrets and variables → Actions → Variables.
- **Perfis padrão:** `docs/data/perfis.json` (fotos em `docs/data/img`). O que você muda no painel fica salvo no navegador.
- **Mexer no painel:** edite `fonte/montar.py` e rode `python3 fonte/montar.py` para gerar `docs/index.html`.

Um "verde" no Actions não garante notícias novas: o resultado de cada coleta aparece no topo do painel e em `docs/data/meta.json`.
