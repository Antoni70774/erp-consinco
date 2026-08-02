"""
Módulo genérico para CONSUMO, PERDA e AVARIA — os três seguem exatamente
o mesmo padrão de dados (baixa de estoque via tipo_operacao + kardex),
mudando apenas a categoria filtrada. Rotas: /api/operacoes/{categoria}/...
categoria ∈ {CONSUMO, PERDA, AVARIA}
"""
from datetime import date, datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from .. import models, schemas, security
from ..database import get_db
from ..inventario_lock import verificar_produto_congelado

router = APIRouter(prefix="/api/operacoes", tags=["Consumo · Perdas · Avarias"], dependencies=[Depends(security.usuario_atual)])

CATEGORIAS_VALIDAS = {"CONSUMO", "PERDA", "AVARIA"}


def _validar_categoria(categoria: str):
    categoria = categoria.upper()
    if categoria not in CATEGORIAS_VALIDAS:
        raise HTTPException(400, f"Categoria inválida. Use uma de: {', '.join(CATEGORIAS_VALIDAS)}")
    return categoria


# ---------------------------------------------------------------------
# Lançamento (baixa de estoque)
# ---------------------------------------------------------------------
@router.post("/lancar")
def lancar(payload: schemas.LancamentoOperacionalIn,
           usuario: models.Usuario = Depends(security.usuario_atual), db: Session = Depends(get_db)):
    produto = db.get(models.Produto, payload.produto_id)
    tipo = db.get(models.TipoOperacao, payload.tipo_operacao_id)
    if not produto or not tipo:
        raise HTTPException(404, "Produto ou tipo de operação não encontrado")
    if tipo.categoria not in CATEGORIAS_VALIDAS:
        raise HTTPException(400, "Esse tipo de operação não é de Consumo, Perda ou Avaria.")

    verificar_produto_congelado(db, payload.empresa_id, payload.produto_id)

    saldo = (
        db.query(models.EstoqueSaldo)
        .filter_by(empresa_id=payload.empresa_id, produto_id=payload.produto_id)
        .first()
    )
    if not saldo or float(saldo.quantidade) < payload.quantidade:
        disponivel = float(saldo.quantidade) if saldo else 0
        raise HTTPException(400, f"Saldo insuficiente. Disponível: {disponivel}")

    saldo.quantidade = float(saldo.quantidade) - payload.quantidade

    mov = models.EstoqueMovimento(
        empresa_id=payload.empresa_id, produto_id=payload.produto_id, tipo_operacao_id=payload.tipo_operacao_id,
        fornecedor_id=payload.fornecedor_id, documento_origem=payload.documento_origem or tipo.codigo,
        motivo=payload.motivo, quantidade=payload.quantidade, valor_unitario=saldo.valor_medio,
        saldo_apos=saldo.quantidade, usuario_id=usuario.id,
    )
    db.add(mov)

    produto.estoque_atual = saldo.quantidade
    db.commit()
    return {"ok": True, "saldo_atual": float(saldo.quantidade)}


# ---------------------------------------------------------------------
# Resumo (KPIs)
# ---------------------------------------------------------------------
@router.get("/{categoria}/resumo")
def resumo(categoria: str, empresa_id: int | None = None, dias: int = 30, db: Session = Depends(get_db)):
    categoria = _validar_categoria(categoria)
    data_inicio = datetime.utcnow() - timedelta(days=dias)

    q = (
        db.query(
            func.coalesce(func.sum(models.EstoqueMovimento.quantidade), 0),
            func.coalesce(func.sum(models.EstoqueMovimento.quantidade * models.EstoqueMovimento.valor_unitario), 0),
            func.count(models.EstoqueMovimento.id),
        )
        .join(models.TipoOperacao, models.TipoOperacao.id == models.EstoqueMovimento.tipo_operacao_id)
        .filter(models.TipoOperacao.categoria == categoria)
        .filter(models.EstoqueMovimento.criado_em >= data_inicio)
    )
    if empresa_id:
        q = q.filter(models.EstoqueMovimento.empresa_id == empresa_id)
    qtd, valor, lancamentos = q.first()

    return {
        "categoria": categoria, "periodo_dias": dias,
        "quantidade_total": float(qtd), "valor_total": float(valor), "lancamentos": lancamentos,
    }


# ---------------------------------------------------------------------
# Por empresa
# ---------------------------------------------------------------------
@router.get("/{categoria}/por-empresa")
def por_empresa(categoria: str, dias: int = 30, db: Session = Depends(get_db)):
    categoria = _validar_categoria(categoria)
    data_inicio = datetime.utcnow() - timedelta(days=dias)

    q = (
        db.query(
            models.Empresa.id, models.Empresa.nome_fantasia, models.Empresa.razao_social,
            func.coalesce(func.sum(models.EstoqueMovimento.quantidade), 0),
            func.coalesce(func.sum(models.EstoqueMovimento.quantidade * models.EstoqueMovimento.valor_unitario), 0),
        )
        .join(models.EstoqueMovimento, models.EstoqueMovimento.empresa_id == models.Empresa.id)
        .join(models.TipoOperacao, models.TipoOperacao.id == models.EstoqueMovimento.tipo_operacao_id)
        .filter(models.TipoOperacao.categoria == categoria)
        .filter(models.EstoqueMovimento.criado_em >= data_inicio)
        .group_by(models.Empresa.id, models.Empresa.nome_fantasia, models.Empresa.razao_social)
    )
    return [{"empresa_id": r[0], "empresa_nome": r[1] or r[2], "quantidade": float(r[3]), "valor_total": float(r[4])} for r in q.all()]


# ---------------------------------------------------------------------
# Por fornecedor (mais relevante em Avarias)
# ---------------------------------------------------------------------
@router.get("/{categoria}/por-fornecedor")
def por_fornecedor(categoria: str, dias: int = 90, db: Session = Depends(get_db)):
    categoria = _validar_categoria(categoria)
    data_inicio = datetime.utcnow() - timedelta(days=dias)

    q = (
        db.query(
            models.Fornecedor.id, models.Fornecedor.razao_social,
            func.coalesce(func.sum(models.EstoqueMovimento.quantidade), 0),
            func.coalesce(func.sum(models.EstoqueMovimento.quantidade * models.EstoqueMovimento.valor_unitario), 0),
        )
        .join(models.EstoqueMovimento, models.EstoqueMovimento.fornecedor_id == models.Fornecedor.id)
        .join(models.TipoOperacao, models.TipoOperacao.id == models.EstoqueMovimento.tipo_operacao_id)
        .filter(models.TipoOperacao.categoria == categoria)
        .filter(models.EstoqueMovimento.criado_em >= data_inicio)
        .group_by(models.Fornecedor.id, models.Fornecedor.razao_social)
    )
    resultado = [{"fornecedor_id": r[0], "fornecedor_nome": r[1], "quantidade": float(r[2]), "valor_total": float(r[3])} for r in q.all()]
    return sorted(resultado, key=lambda x: x["valor_total"], reverse=True)


# ---------------------------------------------------------------------
# Por produto (ranking)
# ---------------------------------------------------------------------
@router.get("/{categoria}/por-produto")
def por_produto(categoria: str, dias: int = 30, empresa_id: int | None = None, limit: int = 50, db: Session = Depends(get_db)):
    categoria = _validar_categoria(categoria)
    data_inicio = datetime.utcnow() - timedelta(days=dias)

    q = (
        db.query(
            models.Produto.id, models.Produto.codigo, models.Produto.descricao,
            func.coalesce(func.sum(models.EstoqueMovimento.quantidade), 0),
            func.coalesce(func.sum(models.EstoqueMovimento.quantidade * models.EstoqueMovimento.valor_unitario), 0),
        )
        .join(models.EstoqueMovimento, models.EstoqueMovimento.produto_id == models.Produto.id)
        .join(models.TipoOperacao, models.TipoOperacao.id == models.EstoqueMovimento.tipo_operacao_id)
        .filter(models.TipoOperacao.categoria == categoria)
        .filter(models.EstoqueMovimento.criado_em >= data_inicio)
    )
    if empresa_id:
        q = q.filter(models.EstoqueMovimento.empresa_id == empresa_id)
    q = q.group_by(models.Produto.id, models.Produto.codigo, models.Produto.descricao)

    resultado = [{"produto_id": r[0], "codigo": r[1], "descricao": r[2], "quantidade": float(r[3]), "valor_total": float(r[4])} for r in q.all()]
    resultado.sort(key=lambda x: x["valor_total"], reverse=True)
    return resultado[:limit]


# ---------------------------------------------------------------------
# Evolução mensal (últimos 12 meses)
# ---------------------------------------------------------------------
@router.get("/{categoria}/evolucao-mensal")
def evolucao_mensal(categoria: str, empresa_id: int | None = None, db: Session = Depends(get_db)):
    categoria = _validar_categoria(categoria)
    data_inicio = date.today().replace(day=1) - timedelta(days=365)

    q = (
        db.query(
            func.date_trunc("month", models.EstoqueMovimento.criado_em).label("mes"),
            func.coalesce(func.sum(models.EstoqueMovimento.quantidade), 0),
            func.coalesce(func.sum(models.EstoqueMovimento.quantidade * models.EstoqueMovimento.valor_unitario), 0),
        )
        .join(models.TipoOperacao, models.TipoOperacao.id == models.EstoqueMovimento.tipo_operacao_id)
        .filter(models.TipoOperacao.categoria == categoria)
        .filter(models.EstoqueMovimento.criado_em >= data_inicio)
    )
    if empresa_id:
        q = q.filter(models.EstoqueMovimento.empresa_id == empresa_id)
    q = q.group_by("mes").order_by("mes")

    return [{"mes": r[0].strftime("%Y-%m"), "quantidade": float(r[1]), "valor_total": float(r[2])} for r in q.all()]


# ---------------------------------------------------------------------
# Lançamentos (lista detalhada / extrato)
# ---------------------------------------------------------------------
@router.get("/{categoria}/lancamentos")
def lancamentos(categoria: str, empresa_id: int | None = None, skip: int = 0, limit: int = 200, db: Session = Depends(get_db)):
    categoria = _validar_categoria(categoria)
    q = (
        db.query(models.EstoqueMovimento, models.Produto, models.TipoOperacao, models.Fornecedor)
        .join(models.Produto, models.Produto.id == models.EstoqueMovimento.produto_id)
        .join(models.TipoOperacao, models.TipoOperacao.id == models.EstoqueMovimento.tipo_operacao_id)
        .outerjoin(models.Fornecedor, models.Fornecedor.id == models.EstoqueMovimento.fornecedor_id)
        .filter(models.TipoOperacao.categoria == categoria)
    )
    if empresa_id:
        q = q.filter(models.EstoqueMovimento.empresa_id == empresa_id)
    q = q.order_by(models.EstoqueMovimento.criado_em.desc()).offset(skip).limit(limit)

    return [{
        "id": m.id, "data": m.criado_em, "produto_codigo": p.codigo, "produto_descricao": p.descricao,
        "tipo_operacao": t.descricao, "fornecedor_nome": f.razao_social if f else None,
        "motivo": m.motivo, "documento_origem": m.documento_origem,
        "quantidade": float(m.quantidade), "valor_unitario": float(m.valor_unitario),
        "valor_total": float(m.quantidade) * float(m.valor_unitario),
    } for m, p, t, f in q.all()]
