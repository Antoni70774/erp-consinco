import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import models, schemas
from .database import engine, garantir_schema
from .routers import auth, compras, estoque, financeiro, gerencial, inventario, operacoes, relatorios, vendas
from .routers.crud_factory import build_crud_router

app = FastAPI(
    title="ERP Consinco-Style",
    description="Sistema de gestão empresarial — módulo Fundação "
                 "(Gerencial, Cadastros, Compras, Financeiro, Usuários, Tipos de Operação).",
    version="0.1.0",
)

# Em produção, defina ALLOWED_ORIGINS com a URL do frontend na nuvem
# (ex: "https://erp-clientex-frontend.up.railway.app"), separadas por vírgula.
# Sem essa variável, libera tudo — ok para testes, não recomendado em produção.
_origins_env = os.getenv("ALLOWED_ORIGINS")
allow_origins = [o.strip() for o in _origins_env.split(",")] if _origins_env else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cria as tabelas automaticamente se ainda não existirem
# (em produção, prefira usar sql/schema.sql + Alembic para migrações controladas)
garantir_schema()
models.Base.metadata.create_all(bind=engine)

app.include_router(auth.router)
app.include_router(gerencial.router)
app.include_router(compras.router)
app.include_router(financeiro.router)
app.include_router(estoque.router)
app.include_router(inventario.router)
app.include_router(operacoes.router)
app.include_router(vendas.router)
app.include_router(relatorios.router)

# ---- Cadastros (CRUD genérico) ----
app.include_router(build_crud_router(
    prefix="/api/empresas", tags=["Empresas"], model=models.Empresa,
    schema_in=schemas.EmpresaIn, schema_out=schemas.EmpresaOut,
    search_fields=["razao_social", "nome_fantasia", "cnpj"],
))

app.include_router(build_crud_router(
    prefix="/api/usuarios", tags=["Usuários"], model=models.Usuario,
    schema_in=schemas.UsuarioIn, schema_out=schemas.UsuarioOut,
    search_fields=["nome", "login"],
))

app.include_router(build_crud_router(
    prefix="/api/tipos-operacao", tags=["Tipos de Operação"], model=models.TipoOperacao,
    schema_in=schemas.TipoOperacaoIn, schema_out=schemas.TipoOperacaoOut,
    search_fields=["descricao", "codigo", "cfop"],
))

app.include_router(build_crud_router(
    prefix="/api/fornecedores", tags=["Fornecedores"], model=models.Fornecedor,
    schema_in=schemas.FornecedorIn, schema_out=schemas.FornecedorOut,
    search_fields=["razao_social", "nome_fantasia", "cnpj_cpf"],
))

app.include_router(build_crud_router(
    prefix="/api/transportadoras", tags=["Transportadoras"], model=models.Transportadora,
    schema_in=schemas.TransportadoraIn, schema_out=schemas.TransportadoraOut,
    search_fields=["razao_social", "cnpj"],
))

app.include_router(build_crud_router(
    prefix="/api/funcionarios", tags=["Funcionários"], model=models.Funcionario,
    schema_in=schemas.FuncionarioIn, schema_out=schemas.FuncionarioOut,
    search_fields=["nome", "matricula", "cpf"],
))

app.include_router(build_crud_router(
    prefix="/api/clientes", tags=["Clientes"], model=models.Cliente,
    schema_in=schemas.ClienteIn, schema_out=schemas.ClienteOut,
    search_fields=["nome", "cnpj_cpf"],
))

app.include_router(build_crud_router(
    prefix="/api/categorias-produto", tags=["Categorias de Produto"], model=models.CategoriaProduto,
    schema_in=schemas.CategoriaProdutoIn, schema_out=schemas.CategoriaProdutoOut,
    search_fields=["descricao", "codigo"],
))

app.include_router(build_crud_router(
    prefix="/api/produtos", tags=["Produtos"], model=models.Produto,
    schema_in=schemas.ProdutoIn, schema_out=schemas.ProdutoOut,
    search_fields=["descricao", "codigo", "codigo_barras"],
))


@app.get("/api/health")
def health():
    return {"status": "ok"}
