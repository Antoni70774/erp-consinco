"""
Popula o banco com dados mínimos para o sistema funcionar no primeiro acesso:
- 1 empresa
- 1 perfil ADMIN + usuário admin/admin123
- Tipos de operação padrão (item 14 do escopo)
- Plano de contas básico
- Algumas categorias de produto

Executar com:  python -m app.seed
"""
from .database import SessionLocal, engine, garantir_schema
from . import models
from .security import hash_senha

garantir_schema()
models.Base.metadata.create_all(bind=engine)
db = SessionLocal()

try:
    if not db.query(models.Empresa).first():
        empresa = models.Empresa(
            codigo="001", razao_social="Minha Empresa Matriz LTDA",
            nome_fantasia="Matriz", cnpj="00.000.000/0001-00",
            tipo="MATRIZ", cidade="Fortaleza", uf="CE",
        )
        db.add(empresa)
        db.flush()

        perfil_admin = models.PerfilAcesso(
            descricao="ADMIN",
            permissoes={"tudo": "rw"},
        )
        db.add(perfil_admin)
        db.flush()

        admin = models.Usuario(
            nome="Administrador", login="admin", email="admin@empresa.com",
            senha_hash=hash_senha("admin123"),
            perfil_id=perfil_admin.id, empresa_id=empresa.id,
        )
        db.add(admin)

        # ---- Tipos de operação (item 14: CFOP por situação) ----
        tipos = [
            dict(codigo="VDA", cfop="5102", descricao="Venda de mercadoria - dentro do estado",
                 categoria="VENDA", natureza="SAIDA", gera_financeiro=True),
            dict(codigo="VDA-FE", cfop="6102", descricao="Venda de mercadoria - fora do estado",
                 categoria="VENDA", natureza="SAIDA", gera_financeiro=True),
            dict(codigo="CMP", cfop="1102", descricao="Compra para comercialização - dentro do estado",
                 categoria="COMPRA", natureza="ENTRADA", gera_financeiro=True),
            dict(codigo="CMP-FE", cfop="2102", descricao="Compra para comercialização - fora do estado",
                 categoria="COMPRA", natureza="ENTRADA", gera_financeiro=True),
            dict(codigo="PRD", cfop="5927", descricao="Baixa de estoque por perda/quebra",
                 categoria="PERDA", natureza="SAIDA", gera_financeiro=False),
            dict(codigo="AVR", cfop="5927", descricao="Baixa de estoque por avaria",
                 categoria="AVARIA", natureza="SAIDA", gera_financeiro=False),
            dict(codigo="TRF-S", cfop="5152", descricao="Transferência de mercadoria - saída",
                 categoria="TRANSFERENCIA", natureza="SAIDA", gera_financeiro=False),
            dict(codigo="TRF-E", cfop="1152", descricao="Transferência de mercadoria - entrada",
                 categoria="TRANSFERENCIA", natureza="ENTRADA", gera_financeiro=False),
            dict(codigo="DEV-V", cfop="1202", descricao="Devolução de venda",
                 categoria="DEVOLUCAO", natureza="ENTRADA", gera_financeiro=True),
            dict(codigo="DEV-C", cfop="5202", descricao="Devolução de compra",
                 categoria="DEVOLUCAO", natureza="SAIDA", gera_financeiro=True),
            dict(codigo="CONS", cfop="5927", descricao="Consumo interno",
                 categoria="CONSUMO", natureza="SAIDA", gera_financeiro=False),
            dict(codigo="BONI", cfop="5910", descricao="Bonificação recebida do fornecedor",
                 categoria="BONIFICACAO", natureza="ENTRADA", gera_financeiro=False),
            dict(codigo="INV-A", cfop="0000", descricao="Ajuste de inventário - sobra",
                 categoria="INVENTARIO", natureza="ENTRADA", gera_financeiro=False),
            dict(codigo="INV-F", cfop="0000", descricao="Ajuste de inventário - falta",
                 categoria="INVENTARIO", natureza="SAIDA", gera_financeiro=False),
        ]
        for t in tipos:
            db.add(models.TipoOperacao(**t))

        # ---- Plano de contas básico ----
        planos = [
            dict(codigo="1.1", descricao="Vendas de Mercadorias", tipo="RECEITA"),
            dict(codigo="2.1", descricao="Compra de Mercadorias", tipo="DESPESA"),
            dict(codigo="2.2", descricao="Despesas com Frete", tipo="DESPESA"),
            dict(codigo="2.3", descricao="Despesas Administrativas", tipo="DESPESA"),
        ]
        for p in planos:
            db.add(models.PlanoConta(**p))

        # ---- Categorias de produto ----
        categorias = ["Mercearia", "Bebidas", "Limpeza", "Hortifruti", "Açougue", "Padaria"]
        for i, c in enumerate(categorias, start=1):
            db.add(models.CategoriaProduto(codigo=f"CAT{i:02d}", descricao=c))

        db.commit()
        print("Seed aplicado com sucesso. Usuário: admin / Senha: admin123")
    else:
        print("Banco já possui dados. Seed não executado (evitar duplicidade).")
finally:
    db.close()
