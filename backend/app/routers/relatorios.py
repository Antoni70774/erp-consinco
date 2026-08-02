from datetime import date, datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from .. import models, security
from ..database import get_db

router = APIRouter(prefix="/api/relatorios", tags=["Relatórios Avançados"], dependencies=[Depends(security.usuario_atual)])


@router.get("/consolidado")
def consolidado(empresa_id: int | None = None, db: Session = Depends(get_db)):
    """
    Relatório gerencial consolidado: cruza Estoque, Vendas, Compras,
    Perdas, Avarias, Consumo e Financeiro num único painel — pensado para
    ser a tela de "fechamento do dia/mês" de uma rede de lojas.
    """
    hoje = date.today()

    def total_kardex(categoria, dias=30):
        data_inicio = datetime.utcnow() - timedelta(days=dias)
        q = (
            db.query(func.coalesce(func.sum(models.EstoqueMovimento.quantidade * models.EstoqueMovimento.valor_unitario), 0))
            .join(models.TipoOperacao, models.TipoOperacao.id == models.EstoqueMovimento.tipo_operacao_id)
            .filter(models.TipoOperacao.categoria == categoria)
            .filter(models.EstoqueMovimento.criado_em >= data_inicio)
        )
        if empresa_id:
            q = q.filter(models.EstoqueMovimento.empresa_id == empresa_id)
        return float(q.scalar() or 0)

    vendas_q = db.query(models.Venda).filter(
        func.extract("month", models.Venda.data_venda) == hoje.month,
        func.extract("year", models.Venda.data_venda) == hoje.year,
        models.Venda.status.in_(["CONCLUIDA", "DEVOLVIDA_PARCIAL"]),
    )
    if empresa_id:
        vendas_q = vendas_q.filter(models.Venda.empresa_id == empresa_id)
    valor_vendas_mes = sum(float(v.valor_total) for v in vendas_q.all())

    compras_q = db.query(func.coalesce(func.sum(models.Compra.valor_total), 0)).filter(
        func.extract("month", models.Compra.data_pedido) == hoje.month,
        func.extract("year", models.Compra.data_pedido) == hoje.year,
    )
    if empresa_id:
        compras_q = compras_q.filter(models.Compra.empresa_id == empresa_id)
    valor_compras_mes = float(compras_q.scalar() or 0)

    estoque_q = db.query(func.coalesce(func.sum(models.EstoqueSaldo.quantidade * models.EstoqueSaldo.valor_medio), 0))
    if empresa_id:
        estoque_q = estoque_q.filter(models.EstoqueSaldo.empresa_id == empresa_id)
    valor_estoque = float(estoque_q.scalar() or 0)

    a_pagar_q = db.query(func.coalesce(func.sum(models.ContaPagar.valor_original), 0)).filter(models.ContaPagar.status == "ABERTO")
    a_receber_q = db.query(func.coalesce(func.sum(models.ContaReceber.valor_original), 0)).filter(models.ContaReceber.status == "ABERTO")
    if empresa_id:
        a_pagar_q = a_pagar_q.filter(models.ContaPagar.empresa_id == empresa_id)
        a_receber_q = a_receber_q.filter(models.ContaReceber.empresa_id == empresa_id)

    return {
        "periodo_referencia": hoje.strftime("%Y-%m"),
        "vendas": {"valor_mes": valor_vendas_mes},
        "compras": {"valor_mes": valor_compras_mes},
        "estoque": {"valor_atual": valor_estoque},
        "perdas": {"valor_30_dias": total_kardex("PERDA")},
        "avarias": {"valor_30_dias": total_kardex("AVARIA")},
        "consumo": {"valor_30_dias": total_kardex("CONSUMO")},
        "financeiro": {
            "a_pagar_aberto": float(a_pagar_q.scalar() or 0),
            "a_receber_aberto": float(a_receber_q.scalar() or 0),
        },
        "margem_bruta_estimada_mes": valor_vendas_mes - valor_compras_mes,
    }
