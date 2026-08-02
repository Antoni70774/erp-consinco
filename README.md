# ERP Consinco-Style — Módulo Fundação

Sistema de gestão empresarial (estilo Consinco/varejo) construído com
**PostgreSQL + FastAPI (Python) + HTML/JS puro**. Esta primeira entrega
cobre a **fundação completa** do sistema, sobre a qual os módulos de
análise (Estoque, Inventário, Consumo, Perdas, Avarias, Vendas) serão
construídos nas próximas fases.

## ✅ O que já está pronto e funcional

| Módulo | Conteúdo |
|---|---|
| **1. Gerencial** | Dashboard com KPIs consolidados (cadastros, compras, financeiro, estoque) |
| **8. Cadastros** | Clientes, Fornecedores, Transportadoras, Funcionários, Empresas/Lojas |
| **9. Produtos** | Cadastro completo: fiscal (NCM, CEST, CFOP, CST ICMS/PIS/COFINS/IPI, MVA), comercial, estoque mínimo/máximo |
| **10. Compras** | Pedido de compra completo (cabeçalho + itens), recebimento com atualização automática de estoque (custo médio) |
| **12. Financeiro** | Contas a pagar e a receber, baixa de títulos, indicadores de atraso e saldo projetado |
| **13. Usuários e senhas** | Login com JWT, senha com hash bcrypt, perfis de acesso |
| **14. Tipos de operação** | Cadastro de CFOP por situação (venda, compra, perda, avaria, transferência, devolução, consumo, bonificação, inventário) — já populado com exemplos |
| **15. Banco de dados** | PostgreSQL real, schema completo em `sql/schema.sql`, com tabelas-âncora (`estoque_saldo`, `estoque_movimentos`) prontas para os próximos módulos |

## 🚧 Roadmap (próximas fases, conforme priorização combinada)

2. **Estoque** — curva ABC, giro, cobertura, ruptura, análise por seção/categoria/fornecedor
3. **Inventário** — abertura por produto/seção, congelamento de estoque, críticas, fechamento
4. **Consumo** — análises de consumo interno
5. **Perdas** — análises de quebra operacional
6. **Avarias** — análises por empresa/fornecedor/lançamento
7. **Vendas** — análise de produto, comparativo mês/ano, por empresa/fornecedor, devoluções
11. **Relatórios** — relatórios gerenciais diversos

A base de dados já foi desenhada para receber esses módulos sem retrabalho
(ver tabela `estoque_movimentos`, que funciona como kardex central).

---

## 🚀 Como rodar (Docker — recomendado)

Pré-requisitos: [Docker](https://www.docker.com/) e Docker Compose instalados.

```bash
cd erp-consinco
docker compose up --build
```

Isso sobe 4 serviços:
- **PostgreSQL** → porta `5432`
- **Backend (API)** → http://localhost:8000 (documentação interativa em `/docs`)
- **Frontend** → http://localhost:8080
- **Adminer** (visualizador de banco) → http://localhost:8081 (sistema: PostgreSQL, servidor: `db`, usuário: `erp_user`, senha: `erp_pass`, banco: `erp_consinco`)

Na primeira subida, o backend roda automaticamente `app/seed.py`, criando:
- Usuário administrador: **login `admin` / senha `admin123`**
- 1 empresa modelo, tipos de operação, plano de contas e categorias de produto

Acesse **http://localhost:8080** e entre com as credenciais acima.

> ⚠️ Troque a senha do admin e o `SECRET_KEY` do `docker-compose.yml` antes de usar em produção.

## 🖥️ Como rodar sem Docker (Postgres local)

```bash
# 1. Crie o banco
createdb erp_consinco
psql erp_consinco -f sql/schema.sql   # opcional: cria o schema manualmente

# 2. Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL="postgresql+psycopg2://SEU_USUARIO:SUA_SENHA@localhost:5432/erp_consinco"
python -m app.seed
uvicorn app.main:app --reload

# 3. Frontend (em outro terminal)
cd frontend
python -m http.server 8080
```

Acesse http://localhost:8080.

---

## 📁 Estrutura do projeto

```
erp-consinco/
├── docker-compose.yml
├── sql/schema.sql              # DDL completo (referência / instalação manual)
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py             # registra todas as rotas
│       ├── database.py         # conexão SQLAlchemy
│       ├── models.py           # todas as tabelas (ORM)
│       ├── schemas.py          # validação Pydantic
│       ├── security.py         # JWT + hash de senha
│       ├── seed.py             # dados iniciais
│       └── routers/
│           ├── auth.py
│           ├── gerencial.py    # dashboard
│           ├── compras.py      # master-detail + recebimento
│           ├── financeiro.py   # contas a pagar/receber
│           └── crud_factory.py # CRUD genérico reaproveitado pelos cadastros
└── frontend/
    ├── index.html              # login
    ├── app.html                # shell (sidebar + conteúdo)
    ├── css/style.css
    └── js/
        ├── api.js              # cliente REST com JWT
        ├── ui.js                # motor de tabela/formulário genérico
        └── app.js               # roteador + views específicas
```

## 🔌 Documentação da API

Com o backend rodando, acesse **http://localhost:8000/docs** — Swagger
interativo com todos os endpoints (gerado automaticamente pelo FastAPI).

## ⚠️ Nota sobre este ambiente de desenvolvimento

Este projeto foi escrito e validado (sintaxe Python e JavaScript) neste
ambiente, mas **não pôde ser executado ponta-a-ponta aqui** porque o
sandbox não tem acesso à internet nem PostgreSQL/Docker instalados. Ele
está pronto para rodar assim que você executar `docker compose up --build`
na sua máquina — se algo precisar de ajuste fino no seu ambiente, me avise
para corrigirmos juntos.

## ☁️ Rodando na nuvem + instalador para o cliente

O sistema foi preparado para rodar 100% na nuvem (backend + banco), com
um app desktop leve que você instala no PC do cliente e que só se conecta
ao servidor — nenhum dado fica salvo localmente.

Veja o passo a passo completo em **[DEPLOY.md](./DEPLOY.md)**:
- Publicar backend + PostgreSQL na nuvem (Railway)
- Publicar o frontend
- Gerar o instalador `.exe`/`.dmg`/`.AppImage` em `desktop-app/`
- Como atender vários clientes diferentes

## Próximo passo sugerido

Depois de você validar esta fundação rodando localmente, seguimos para o
**módulo de Estoque** (item 2), já conectado ao kardex (`estoque_movimentos`)
criado aqui — incluindo curva ABC, giro, cobertura e ruptura por
seção/categoria/empresa.
