# Gestão Rikletz

Sistema interno de gestão: controle de estoque, cadastro de clientes (PF/PJ) e registro de notas fiscais recebidas (com extração automática de dados a partir do PDF).

Stack: Django + Postgres, rodando em containers Docker. Interface web própria (sem admin do Django como interface principal — o admin fica disponível como atalho de cadastro auxiliar em `/admin/`).

> Retomando o projeto numa sessão nova? Veja **[HANDOFF.md](HANDOFF.md)** — histórico completo do que foi construído, decisões técnicas, bugs já corrigidos e o que falta.

## Módulos

- **Estoque** (`/estoque/`) — peças cadastradas (nome, categoria, preço, imagem, código interno/externo) e controle de quantidade por unidade (Tomás / Ricardo), com busca e filtros ao vivo.
- **Clientes** (`/clientes/`) — pessoas físicas e jurídicas, com validação real de CPF/CNPJ e autopreenchimento de endereço via CEP.
- **Notas Fiscais** (`/notas-fiscais/`) — upload do PDF da NF, extração automática de número, cliente, valores, chave de acesso e itens (ver `backend/notas_fiscais/extracao.py`), com tela de revisão antes de salvar.

## Rodando do zero

Pré-requisitos: Docker + Docker Compose na máquina/VM de destino.

1. Copie `.env.example` para `.env` e preencha os valores reais (gere uma `DJANGO_SECRET_KEY` e senhas fortes — **nunca** commite o `.env`).
2. Ajuste `DJANGO_ALLOWED_HOSTS` e `DJANGO_CSRF_TRUSTED_ORIGINS` no `.env` para o IP/domínio real do servidor.
3. No `docker-compose.yml`, os volumes de dados apontam para `/opt/docker/appdata/gestao/...` — ajuste esse caminho se for rodar em outro servidor.
4. Build e subida:
   ```bash
   docker compose build
   docker compose up -d
   ```
5. Na primeira subida, o `entrypoint.sh` do container `web` roda as migrations, coleta os arquivos estáticos e cria o superusuário do Django automaticamente (usando `DJANGO_SUPERUSER_*` do `.env`).
6. Acesse `http://<host>:8100/`.

## Variáveis de ambiente (`.env`)

Ver `.env.example` para a lista completa. Resumo:

| Variável | Descrição |
|---|---|
| `DJANGO_SECRET_KEY` | Chave secreta do Django (gerar uma nova por ambiente) |
| `DJANGO_DEBUG` | `true`/`false` |
| `DJANGO_ALLOWED_HOSTS` | Hosts permitidos, separados por vírgula |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | Origens confiáveis pra CSRF (com esquema, ex: `http://192.168.0.191:8100`) |
| `POSTGRES_DB` / `POSTGRES_USER` / `POSTGRES_PASSWORD` | Credenciais do banco |
| `DJANGO_SUPERUSER_USERNAME` / `_EMAIL` / `_PASSWORD` | Superusuário criado automaticamente no primeiro start |

## Atualizando o deploy (Portainer)

Este repositório é a fonte de verdade. O deploy em produção roda como uma **Stack Git no Portainer**, apontando pra este repositório (branch `main`, arquivo `docker-compose.yml` na raiz). As variáveis de ambiente reais ficam configuradas diretamente na Stack do Portainer (nunca no Git).

Fluxo de atualização: alterar código → commit → push → no Portainer, atualizar a Stack (pull + redeploy).

## Estrutura

```
backend/
  config/          # settings, urls, wsgi
  estoque/         # peças, categorias, unidades, itens de estoque
  clientes/        # cadastro de clientes PF/PJ
  notas_fiscais/   # registro de NFs + extração automática de PDF
  templates/       # templates compartilhados (base.html com a sidebar) e por app
  static/          # CSS, JS (htmx vendorizado, autofill de CEP)
docker-compose.yml
Dockerfile         # dentro de backend/
```
