# Deploy em Nuvem + App Desktop do Cliente

Este guia leva o sistema do zero até: **backend + banco rodando 24h na nuvem**
e um **instalador .exe** que qualquer técnico roda no PC do cliente,
digitando apenas o endereço do servidor uma vez.

> ⚠️ Não tenho acesso à internet nem a credenciais de nuvem neste ambiente,
> então não consigo publicar por você — mas os passos abaixo são diretos
> e o projeto já está pronto para isso (variáveis de ambiente, Dockerfile,
> CORS configurável etc.).

---

## Visão geral da arquitetura

```
   PC do Cliente                         Nuvem (Railway)
 ┌──────────────────┐                 ┌──────────────────────┐
 │  App Desktop      │   HTTPS         │  Frontend (estático)  │
 │  (Electron .exe)  │ ───────────────▶│  Backend (FastAPI)    │
 │  só abre a URL     │                 │  PostgreSQL (dados)   │
 └──────────────────┘                 └──────────────────────┘
```

Nada fica salvo no PC do cliente (exceto o endereço do servidor, salvo
uma vez). Todos os dados (produtos, compras, financeiro etc.) moram no
PostgreSQL na nuvem.

---

## Passo 1 — Criar conta no Railway

1. Acesse https://railway.app e crie uma conta (pode usar GitHub).
2. Railway cobra por uso; para este sistema, o plano inicial (~US$ 5/mês
   de crédito incluso no plano Hobby) é suficiente para começar.

## Passo 2 — Subir o código para o GitHub

O Railway faz deploy a partir de um repositório Git.

```bash
cd erp-consinco
git init
git add .
git commit -m "ERP Consinco-style - fundação"
# crie um repositório vazio no GitHub e depois:
git remote add origin https://github.com/SEU_USUARIO/erp-consinco.git
git branch -M main
git push -u origin main
```

## Passo 3 — Criar o banco PostgreSQL no Railway

1. No painel do Railway: **New Project → Provision PostgreSQL**.
2. Railway cria o banco e gera automaticamente a variável `DATABASE_URL`.

## Passo 4 — Publicar o backend

1. No mesmo projeto: **New → Deploy from GitHub repo** → selecione o repositório.
2. Em **Settings → Root Directory**, defina `backend` (é onde está o `Dockerfile`).
3. Em **Variables**, adicione:
   - `DATABASE_URL` → clique em "Add Reference" e aponte para a variável do
     serviço PostgreSQL (Railway conecta automaticamente).
   - `SECRET_KEY` → gere uma chave forte, ex: rode `openssl rand -hex 32`
     no seu terminal e cole o resultado.
   - `ALLOWED_ORIGINS` → deixe em branco por enquanto (ajustamos no Passo 6).
4. Clique em **Deploy**. Railway vai construir a imagem Docker e subir o
   backend. Ele já roda o `seed.py` automaticamente na primeira subida
   (usuário `admin` / senha `admin123` — **troque depois**).
5. Em **Settings → Networking → Generate Domain**, gere uma URL pública,
   por exemplo: `erp-clientex-backend.up.railway.app`.
6. Teste abrindo `https://erp-clientex-backend.up.railway.app/docs` no
   navegador — deve aparecer a documentação Swagger da API.

## Passo 5 — Publicar o frontend

O frontend é só HTML/CSS/JS estático. Duas opções:

**Opção A — Railway (mesmo projeto, mais simples de gerenciar):**
1. **New → Deploy from GitHub repo** (mesmo repositório) novamente.
2. **Root Directory** → `frontend`.
3. Como não há build (é HTML puro), configure o **Start Command** como:
   `npx serve -s . -l $PORT`
4. Gere o domínio público em **Settings → Networking**, ex:
   `erp-clientex.up.railway.app`.

**Opção B — Netlify/Vercel (grátis, ainda mais simples para site estático):**
1. Conecte o repositório, aponte a pasta `frontend` como raiz de publicação.
2. Deploy automático a cada push no GitHub.

## Passo 6 — Conectar frontend ↔ backend

1. Edite `frontend/js/config.js` e troque:
   ```js
   window.ERP_CONFIG = {
     API_BASE: "https://erp-clientex-backend.up.railway.app",
     CLIENTE_NOME: "Cliente Exemplo LTDA",
   };
   ```
2. Faça commit e push — o Railway/Netlify republica sozinho.
3. Volte no backend (Railway) e defina `ALLOWED_ORIGINS` com a URL do
   frontend, ex: `https://erp-clientex.up.railway.app` (evita chamadas de
   sites não autorizados à sua API).
4. Redeploy do backend para aplicar a variável.

## Passo 7 — Testar

Abra `https://erp-clientex.up.railway.app` no navegador → deve aparecer
a tela de login e funcionar normalmente, agora 100% na nuvem.

---

## Passo 8 — Gerar o instalador para o cliente (app desktop)

O app em `desktop-app/` é um "navegador dedicado": ao abrir, pede o
endereço do servidor uma única vez e depois sempre abre direto nele.

```bash
cd desktop-app
npm install
npm run dist:win     # gera instalador Windows (.exe) em desktop-app/dist
# npm run dist:mac   # gera .dmg
# npm run dist:linux # gera .AppImage
```

No PC do cliente:
1. Rode o instalador gerado (ex: `ERP Sistema de Gestão Setup 1.0.0.exe`).
2. Ele cria um atalho na área de trabalho.
3. Na primeira abertura, digite o endereço do frontend na nuvem
   (ex: `erp-clientex.up.railway.app`) e clique em Conectar.
4. Pronto — todo acesso seguinte já abre direto no sistema.

> Se quiser trocar o cliente conectado a esse mesmo instalador (ex: usar o
> mesmo .exe em vários clientes), use o botão **"Trocar servidor"** que
> aparece no rodapé do menu lateral dentro do app.

---

## Vários clientes diferentes (multi-empresa/SaaS)

Hoje cada cliente = 1 backend + 1 banco na nuvem (isolamento total, mais
simples e seguro para começar). Para vender a vários clientes:

- Repita os Passos 3–6 para cada cliente novo (backend + banco próprios),
  usando o mesmo código-fonte.
- O mesmo instalador do app desktop (Passo 8) serve para todos — muda
  apenas o endereço digitado na primeira tela.
- Quando o número de clientes crescer, dá pra evoluir para um modelo
  multi-tenant (1 backend só, com um campo `tenant_id` separando os dados
  de cada cliente no banco) — me avise quando chegar nesse ponto que
  ajusto a arquitetura.

## Backups

No Railway, o PostgreSQL tem snapshots automáticos, mas configure também
backups próprios:
```bash
pg_dump "postgresql://usuario:senha@host:porta/banco" > backup-$(date +%Y%m%d).sql
```
Agende isso (ex: cron, GitHub Actions) para rodar diariamente.
