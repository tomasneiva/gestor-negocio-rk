# Handoff — Sistema de Gestão Rikletz

Documento de continuidade do projeto. Objetivo: qualquer pessoa (ou sessão de IA) que pegue esse projeto do zero consiga entender o que existe, por que foi feito assim, e o que falta, sem depender do histórico de conversa.

Última atualização: 2026-09-29.

## 1. O que é o projeto

Sistema interno de gestão pra Rikletz (não é SaaS, uso próprio): controle de estoque, cadastro de clientes, registro de notas fiscais recebidas e pedidos de venda. Rodando self-hosted, num servidor Docker/Portainer do próprio usuário, do mesmo jeito que ele já roda Sonarr/Radarr/Jellyfin etc.

Módulos planejados originalmente: estoque, notas fiscais (registro, não emissão), pedidos de venda, relatórios gerenciais. **Só falta relatórios gerenciais agora.**

## 2. Stack e decisões de arquitetura

- **Backend**: Django 5.1 + Postgres 16. Escolhido em vez de API+frontend separado ou low-code (NocoDB/Baserow) porque o sistema é CRUD-pesado com relatórios, e o admin do Django dá cadastro rápido de graça enquanto as telas customizadas não existem.
- **Servidor web**: Gunicorn + Whitenoise (serve estático direto do processo Django, sem Nginx separado — decisão de simplicidade pra essa escala).
- **Interatividade sem SPA**: HTMX vendorizado localmente em `backend/static/vendor/htmx.min.js` (v2.0.4, sem CDN). Usado pra busca/filtro/ordenação ao vivo (ex: painel de estoque) sem reload de página e sem precisar de build step de frontend.
- **Imagens**: Pillow, usado em `estoque/imaging.py` pra padronizar fotos de peças (recorte central 1:1 + resize 1024×1024).
- **Extração de PDF**: pdfplumber, usado em `notas_fiscais/extracao.py` pra ler DANFEs (nota fiscal eletrônica brasileira) — texto, não OCR (funciona porque DANFE é PDF nativo, não escaneado).
- **Geração de PDF**: reportlab (Platypus), usado em `pedidos/pdf.py` pra gerar o PDF do pedido de venda. Escolhido em vez de WeasyPrint porque é pip-only (não exige libs de sistema tipo cairo/pango no Dockerfile).
- **Sem frontend framework**: templates Django server-side + CSS próprio (`backend/static/css/app.css`, paleta neutra + acento indigo `#4f46e5`) + JS vanilla onde precisou (autofill de CEP).

### Layout base

`backend/templates/base.html` — barra lateral esquerda fixa (232px, escura) com links pros módulos, área de conteúdo à direita. Módulos ativos ficam destacados via `request.resolver_match.app_name`. Cada app tem seus templates em `backend/templates/<app>/`.

## 3. Módulos implementados

### 3.1 Estoque (`backend/estoque/`)

- **Modelos**: `Unidade` (só "Tomás" e "Ricardo", criadas via migration de seed `0002_seed_unidades.py`), `Categoria`, `Peca` (nome, categoria, preço, imagem, código interno "ref", código externo até 13 dígitos numéricos), `EstoqueItem` (peça + unidade + quantidade, par único).
- **Painel** (`/estoque/`): escolha de unidade em abas, busca por nome ao vivo (debounce 400ms via htmx, sem precisar de Enter), filtro por categoria, ordenação por nome/categoria/preço. Backend em `estoque/views.py` (`painel` + endpoint parcial `tabela` que o htmx chama).
- **Cadastro de peças fora do admin** (`/estoque/pecas/`, `/estoque/pecas/nova/`, `/estoque/pecas/<id>/editar/`): formulário com upload de imagem (padronizada automaticamente, ver `estoque/imaging.py::padronizar_imagem`), preço aceitando vírgula/ponto brasileiro.
- Quantidade por unidade ainda só é editável via admin (`/admin/`, inline na tela de Peça) — não tem tela custom pra isso ainda.

### 3.2 Clientes (`backend/clientes/`)

- **Modelo `Cliente`**: PF/PJ (`tipo_pessoa`). Únicos campos obrigatórios: **nome, CEP, CPF/CNPJ**. Resto é opcional: endereço completo, telefone, email, nome do representante, observações.
- **Validação real de CPF/CNPJ** (dígito verificador, não só formato/regex) em `clientes/validators.py`, chamada em `Cliente.clean()` — vale tanto no form quanto no admin quanto em qualquer criação programática que chame `full_clean()`.
- **Autofill de endereço via CEP**: `static/js/clientes.js`, JS vanilla, consulta a API pública ViaCEP no navegador do usuário (precisa de internet no client, não no servidor).
- Telas: `/clientes/`, `/clientes/novo/`, `/clientes/<id>/editar/`.
- `documento` e `cep` são guardados só com dígitos no banco; exibição formatada via properties `documento_formatado` / `cep_formatado`.

### 3.3 Notas Fiscais (`backend/notas_fiscais/`)

- **Fluxo em duas telas**: `/notas-fiscais/enviar/` (só upload do PDF) processa o arquivo e redireciona pra `/notas-fiscais/<id>/editar/` (revisão com tudo já preenchido, editável antes de confirmar).
- **Modelos**: `NotaFiscal` (cliente FK, número, série, data emissão, valor produtos, desconto, valor total, chave de acesso, natureza da operação, observações, texto bruto extraído guardado pra referência/debug) e `NotaFiscalItem` (itens extraídos: código, descrição, NCM, CFOP, unidade, quantidade, valores).
- **Extração automática** (`notas_fiscais/extracao.py`, via pdfplumber): chave de acesso, número, série, natureza da operação, data emissão, valor produtos/desconto/total, dados do cliente (nome, CPF/CNPJ, CEP, cidade, UF), e todos os itens da nota.
- **Auto-cadastro de cliente**: se o CPF/CNPJ extraído não bate com nenhum cliente já cadastrado, um novo `Cliente` é criado automaticamente a partir dos dados extraídos, passando pela validação real de CPF/CNPJ (`full_clean()`). Se a validação falhar (erro de extração), o cliente não é criado e fica em branco pra seleção manual na revisão.
- **Validado ponta a ponta** contra uma NF real (DANFE padrão SEFAZ) — todos os campos e os itens bateram certinho.

#### Achado técnico importante sobre a extração de PDF

`pdfplumber`'s `extract_text()` (sem `layout=True`) "achata" caixas lado a lado do DANFE numa única linha de texto — ex: o rótulo "Natureza da operação" cola com "Protocolo de autorização de uso" que fica ao lado dele no PDF. Regex ingênua de "rótulo seguido do valor" falha nesses campos.

Soluções usadas (documentadas no topo de `extracao.py` também):
1. **Chave de acesso, CPF/CNPJ, CEP, UF**: buscar pelo **formato** do valor (regex de dígitos/pontuação), não pelo rótulo adjacente — mais robusto porque esses formatos são inconfundíveis.
2. **Cálculo do imposto** (valor produtos/desconto/total): a ORDEM dos campos nessa caixa é padronizada nacionalmente pela SEFAZ — a extração pega a linha de valores por **posição**, não por rótulo.
3. **Itens da nota fiscal**: o texto achatado por sorte mantém um item por linha de forma limpa (é uma tabela de coluna única no fluxo de leitura), então regex direto funciona bem aí sem truque nenhum.

Se a extração precisar de ajuste pra outros modelos de NF/DANFE (layouts variam por software emissor, mas os rótulos são padronizados nacionalmente), esse é o ponto de partida — testar contra um PDF real seguindo o mesmo método usado aqui (ver seção 6).

### 3.4 Pedidos de Venda (`backend/pedidos/`)

- **Modelos**: `PedidoVenda` (cliente FK, unidade FK, status, desconto, observações) e `PedidoVendaItem` (peça FK, quantidade, preço unitário **snapshot no momento do pedido** — não segue o preço atual da peça se ela mudar depois).
- **Fluxo de status**: `RASCUNHO → CONFIRMADO → CANCELADO`.
  - Só dá pra editar itens/dados enquanto está em `RASCUNHO` (`pode_editar`).
  - Confirmar exige pelo menos 1 item (`confirmar()` levanta `ValidationError` senão).
  - Cancelar é permitido a partir de `RASCUNHO` ou `CONFIRMADO`; se o pedido já tinha baixa de estoque lançada, cancelar **desfaz a baixa automaticamente** antes de marcar como cancelado (pra nunca deixar estoque descontado de um pedido cancelado).
- **Baixa de estoque é uma ação manual e separada da confirmação** (decisão explícita do usuário: confirmar o pedido não baixa estoque sozinho). Só é possível dar baixa com o pedido `CONFIRMADO` e que ainda não tenha baixa lançada (`pode_dar_baixa`). Tem botão de "Desfazer baixa" enquanto não for desfeita (`pode_desfazer_baixa`).
  - `PedidoVenda.dar_baixa_estoque()`: decrementa `EstoqueItem.quantidade` de cada item na unidade do pedido. Se o estoque disponível for menor que a quantidade pedida, dá baixa só do que tem (clampa em zero, não deixa quantidade negativa) e devolve uma lista de avisos (mostrados como mensagens `warning` na tela). A quantidade efetivamente baixada de cada item fica salva em `PedidoVendaItem.quantidade_baixada` — é esse valor (não a quantidade pedida) que é usado pra reverter depois, senão "desfazer" devolveria estoque a mais em casos de baixa parcial.
  - `PedidoVenda.desfazer_baixa_estoque()`: devolve exatamente `quantidade_baixada` de cada item ao `EstoqueItem` e limpa os campos.
- **Geração de PDF** (`/pedidos/<id>/pdf/`): via `pedidos/pdf.py` (reportlab), disponível em qualquer status.
- **Formulário de itens**: `inlineformset_factory` (Django puro, sem lib extra) com botão "+ Adicionar item" em JS vanilla (`static/js/pedidos.js`) que clona o `formset.empty_form` (padrão `__prefix__`) — mesmo esquema usado pelo Django admin pra formsets dinâmicos. O `<select>` de peça é um widget customizado (`PecaSelectComPreco` em `pedidos/forms.py`) que embute o preço de cada peça como `data-preco` em cada `<option>`; o JS lê esse atributo e preenche o campo de preço unitário automaticamente ao trocar a peça (só se o campo estiver vazio — não sobrescreve preço editado manualmente).
- **Testado ponta a ponta** via script de integração rodado num Postgres efêmero na VM (criar pedido pelo formset, confirmar, dar baixa com estoque insuficiente em uma das peças, desfazer, cancelar com baixa automática revertida, gerar PDF) — todos os cenários passaram antes do deploy.

## 4. Bugs reais encontrados e corrigidos (não reintroduzir)

1. **`STORAGES` no `settings.py` precisa de uma chave `"default"`** (`FileSystemStorage`) além de `"staticfiles"` — sem isso, qualquer upload de arquivo (`ImageField`/`FileField`) quebra com `InvalidStorageError` no Django 5.1.
2. **`DecimalField` em formulário Django não aceita vírgula decimal por padrão**, mesmo com `LANGUAGE_CODE="pt-br"` — precisa `localize=True` no campo do form **e** `USE_THOUSAND_SEPARATOR=True` no settings pra aceitar formatos tipo `1.234,56`.
3. **Mídia (`MEDIA_URL`) não é servida automaticamente com `DEBUG=False`** — foi adicionado um `path("media/<path:path>", serve_static, ...)` manual em `config/urls.py`. Aceitável pra essa escala de app interno (poucos usuários, LAN); não é a forma correta pra produção de alto tráfego (aí seria Nginx/S3/etc).
4. **`.create()` do Django não roda `Model.clean()`** — a criação automática de `Cliente` a partir de dados extraídos de PDF usa `full_clean()` explícito antes de salvar, senão a validação de CPF/CNPJ seria pulada nesse caminho.

## 5. Infraestrutura e deploy

- **Servidor**: VM Ubuntu 24.04 em Proxmox, IP `192.168.0.191` (LAN, não exposto à internet), hostname `proxvm-docker`, já rodando outras stacks Docker (Sonarr/Radarr/Jellyfin/etc) geridas via Portainer.
- **Repositório**: [github.com/tomasneiva/gestor-negocio-rk](https://github.com/tomasneiva/gestor-negocio-rk) — **público**. `.env` nunca é commitado (`.gitignore` cobre isso); só existe `.env.example` com placeholders no repo.
- **Deploy em produção**: Stack Git do Portainer chamada `gestao` — build method "Repository", aponta pro repo acima, branch `main`, compose file `docker-compose.yml` na raiz. As variáveis de ambiente reais (secret key, senha do Postgres, senha do admin) ficam preenchidas direto na configuração da Stack no Portainer, **nunca no Git**.
- **GitOps polling**: configurado pra **72h** (de propósito, pra não ficar consultando o GitHub toda hora). Isso significa que **um push não atualiza o site sozinho** dentro de um prazo curto — é preciso:
  1. Dar push no `main`.
  2. Abrir a Stack `gestao` no Portainer e clicar em **"Pull and redeploy"**.
  3. Leva ~30-60s pra rebuildar a imagem e recriar o container.
- **Dados persistentes**: fora do container, em `/opt/docker/appdata/gestao/{postgres,media,static}` no host — sobrevivem a qualquer redeploy/rebuild da stack.
- **Acesso**: `http://192.168.0.191:8100/` (redireciona pra `/estoque/`). Admin em `/admin/`. Health check em `/health/`.
- A pasta antiga `/opt/docker/gestao/` (deploy manual via scp, usado antes da migração pro Portainer) foi removida do servidor — não existe mais, não usar como referência.

## 6. Como continuar o desenvolvimento numa sessão nova

1. **Código local**: `D:\claude\gestao\` neste PC Windows. É o mesmo diretório usado pra gerar tudo até agora.
2. **Acesso à VM**: SSH configurado — `ssh vmdocker` a partir do Git Bash (alias já em `~/.ssh/config`, chave em `~/.ssh/vmdocker_ed25519`). Usuário `vmdocker` está no grupo `docker`, não precisa de sudo pra comandos docker.
3. **Editar e testar mudanças de código**:
   - Editar os arquivos em `D:\claude\gestao\backend\`.
   - Pra testar contra um banco real antes de dar push, dá pra `scp` os arquivos alterados pra dentro do container via `docker cp`, ou levantar uma stack local — mas o método usado até agora foi testar direto no servidor (via `docker compose exec`/`docker compose run` na VM), já que não há ambiente de desenvolvimento local separado configurado.
4. **Gerar novas migrations** (models novos ou alterados): não dá pra rodar `makemigrations` localmente sem Django instalado nesse Windows. Como o deploy é via Portainer (não existe mais `/opt/docker/gestao/`), o método atual é buildar uma imagem temporária direto na VM, num diretório descartável, sem tocar nos containers de produção (`gestao-web`/`gestao-db`):
   ```bash
   # 1. copia o código atualizado (com o model novo) pra um dir temporário na VM
   cd /d/claude/gestao
   tar -czf - backend | ssh vmdocker "rm -rf /tmp/gestao-mkmig && mkdir -p /tmp/gestao-mkmig && tar -xzf - -C /tmp/gestao-mkmig"

   # 2. builda uma imagem temporária a partir desse código
   ssh vmdocker "cd /tmp/gestao-mkmig/backend && docker build -t gestao-mkmig-tmp ."

   # 3. roda makemigrations (não precisa de banco real nem de rede — makemigrations só lê os arquivos de migration existentes)
   ssh vmdocker "docker rm -f gestao-mkmig 2>/dev/null; docker run --name gestao-mkmig --entrypoint python gestao-mkmig-tmp manage.py makemigrations <app>"

   # 4. copia o arquivo gerado de volta
   ssh vmdocker "docker cp gestao-mkmig:/app/<app>/migrations/000X_xxx.py /tmp/gestao-mkmig/"
   scp vmdocker:/tmp/gestao-mkmig/000X_xxx.py backend/<app>/migrations/

   # 5. limpa tudo (container, imagem, diretório temporário) — nada disso é persistente nem afeta produção
   ssh vmdocker "docker rm -f gestao-mkmig; docker rmi gestao-mkmig-tmp; rm -rf /tmp/gestao-mkmig"
   ```
   Pra validar de verdade antes de dar push (recomendado quando o model é novo/mexe em lógica de negócio), dá pra subir também um Postgres efêmero isolado numa rede Docker própria (`docker network create gestao-mkmig-net` + `docker run -d --name gestao-mkmig-db --network gestao-mkmig-net -e POSTGRES_DB=... postgres:16-alpine`), rodar `migrate` contra ele com a imagem temporária, e então rodar um script de teste via `manage.py shell -c "exec(open('/app/test.py').read())"` usando `django.test.Client` pra exercitar as views de ponta a ponta. Tudo isolado (nomes `gestao-mkmig-*`, rede própria, sem volume) — não encosta em `gestao-db`/`gestao-web` de produção. Foi assim que o módulo de pedidos foi validado antes do primeiro deploy.
5. **Publicar uma mudança**:
   ```bash
   cd /d/claude/gestao
   git add -A && git commit -m "..."
   git push origin main
   ```
   `git push` costuma ser bloqueado pelo classificador de modo automático do Claude Code mesmo com confirmação em texto do usuário — se acontecer, tentar de novo uma vez, ou pedir pro usuário rodar via `! <comando>` no prompt.
   Depois do push, **avisar o usuário pra clicar em "Pull and redeploy" na Stack `gestao` do Portainer** (não acontece sozinho por causa do polling de 72h).
6. **Verificar que subiu**: `curl http://192.168.0.191:8100/health/` deve responder `{"status": "ok"}`. Conferir dados existentes não sumiram (ex: `curl http://192.168.0.191:8100/estoque/pecas/`).

## 7. O que falta

- **Relatórios gerenciais** — módulo inteiro, não começado.
- **Exclusão pela UI** de peças, clientes, notas fiscais e pedidos — só existe via `/admin/` hoje.
- **Edição manual dos itens de uma NF** já registrada (hoje só é possível ver, não editar linha a linha depois de salva).
- **Backup do Postgres** — não configurado; dados vivem só em `/opt/docker/appdata/gestao/postgres/` no host, sem rotina de backup automatizada.
- **Ambiente de desenvolvimento local** — hoje todo teste de mudança de backend é feito direto no servidor (VM), não há Postgres/Docker local no Windows do usuário. Se o projeto crescer, vale considerar montar isso.
