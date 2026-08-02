from datetime import date
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from .. import models, security
from ..database import get_db

router = APIRouter(prefix="/api/gerencial", tags=["Módulo Gerencial"], dependencies=[Depends(security.usuario_atual)])


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db)):
    hoje = date.today()

    total_produtos = db.query(func.count(models.Produto.id)).filter(models.Produto.ativo.is_(True)).scalar() or 0
    total_fornecedores = db.query(func.count(models.Fornecedor.id)).filter(models.Fornecedor.ativo.is_(True)).scalar() or 0
    total_clientes = db.query(func.count(models.Cliente.id)).filter(models.Cliente.ativo.is_(True)).scalar() or 0
    total_empresas = db.query(func.count(models.Empresa.id)).filter(models.Empresa.ativo.is_(True)).scalar() or 0

    compras_abertas = db.query(func.count(models.Compra.id)).filter(models.Compra.status == "ABERTO").scalar() or 0
    valor_compras_mes = (
        db.query(func.coalesce(func.sum(models.Compra.valor_total), 0))
        .filter(func.extract("month", models.Compra.data_pedido) == hoje.month)
        .filter(func.extract("year", models.Compra.data_pedido) == hoje.year)
        .scalar() or 0
    )

    a_pagar_aberto = (
        db.query(func.coalesce(func.sum(models.ContaPagar.valor_original), 0))
        .filter(models.ContaPagar.status == "ABERTO").scalar() or 0
    )
    a_receber_aberto = (
        db.query(func.coalesce(func.sum(models.ContaReceber.valor_original), 0))
        .filter(models.ContaReceber.status == "ABERTO").scalar() or 0
    )

    valor_estoque = (
        db.query(func.coalesce(func.sum(models.EstoqueSaldo.quantidade * models.EstoqueSaldo.valor_medio), 0))
        .scalar() or 0
    )

    produtos_abaixo_minimo = (
        db.query(func.count(models.Produto.id))
        .filter(models.Produto.ativo.is_(True))
        .filter(models.Produto.estoque_atual < models.Produto.estoque_minimo)
        .scalar() or 0
    )

    return {
        "cadastros": {
            "produtos_ativos": total_produtos,
            "fornecedores_ativos": total_fornecedores,
            "clientes_ativos": total_clientes,
            "empresas_ativas": total_empresas,
        },
        "compras": {
            "pedidos_em_aberto": compras_abertas,
            "valor_comprado_mes_atual": float(valor_compras_mes),
        },
        "financeiro": {
            "contas_a_pagar_aberto": float(a_pagar_aberto),
            "contas_a_receber_aberto": float(a_receber_aberto),
            "saldo_projetado": float(a_receber_aberto) - float(a_pagar_aberto),
        },
        "estoque": {
            "valor_total_estoque": float(valor_estoque),
            "produtos_abaixo_minimo": produtos_abaixo_minimo,
        },
        "modulos_em_construcao": [
            "Estoque (análises avançadas)", "Inventário", "Consumo", "Perdas",
            "Avarias", "Vendas", "Relatórios avançados",
        ],
    }
