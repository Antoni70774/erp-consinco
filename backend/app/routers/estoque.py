"""
Módulo de Estoque — análises usadas por redes de varejo:
- Saldo por produto/empresa
- Curva ABC (classificação por valor de estoque)
- Giro de estoque e Cobertura (dias)
- Ruptura / abaixo do mínimo
- Kardex (extrato de movimentações)
- Ajuste manual de saldo
"""
from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from .. import models, security
from ..database import get_db
from ..inventario_lock import verificar_produto_congelado

router = APIRouter(prefix="/api/estoque", tags=["Estoque"], dependencies=[Depends(security.usuario_atual)])


# ---------------------------------------------------------------------
# Saldo por produto / empresa
# ---------------------------------------------------------------------
@router.get("/saldo")
def saldo(empresa_id: int | None = None, categoria_id: int | None = None,
          apenas_com_estoque: bool = False, db: Session = Depends(get_db)):
    q = (
        db.query(models.EstoqueSaldo, models.Produto, models.Empresa)
        .join(models.Produto, models.Produto.id == models.EstoqueSaldo.produto_id)
        .join(models.Empresa, models.Empresa.id == models.EstoqueSaldo.empresa_id)
    )
    if empresa_id:
        q = q.filter(models.EstoqueSaldo.empresa_id == empresa_id)
    if categoria_id:
        q = q.filter(models.Produto.categoria_id == categoria_id)
    if apenas_com_estoque:
        q = q.filter(models.EstoqueSaldo.quantidade > 0)

    resultado = []
    for saldo_row, produto, empresa in q.all():
        valor_total = float(saldo_row.quantidade) * float(saldo_row.valor_medio)
        resultado.append({
            "produto_id": produto.id,
            "produto_codigo": produto.codigo,
            "produto_descricao": produto.descricao,
            "empresa_id": empresa.id,
            "empresa_nome": empresa.nome_fantasia or empresa.razao_social,
            "quantidade": float(saldo_row.quantidade),
            "valor_medio": float(saldo_row.valor_medio),
            "valor_total": valor_total,
            "estoque_minimo": float(produto.estoque_minimo or 0),
            "estoque_maximo": float(produto.estoque_maximo or 0),
            "abaixo_minimo": float(saldo_row.quantidade) < float(produto.estoque_minimo or 0),
        })
    return resultado


# ---------------------------------------------------------------------
# Ruptura / abaixo do mínimo
# ---------------------------------------------------------------------
@router.get("/ruptura")
def ruptura(empresa_id: int | None = None, db: Session = Depends(get_db)):
    q = (
        db.query(models.EstoqueSaldo, models.Produto, models.Empresa)
        .join(models.Produto, models.Produto.id == models.EstoqueSaldo.produto_id)
        .join(models.Empresa, models.Empresa.id == models.EstoqueSaldo.empresa_id)
        .filter(models.EstoqueSaldo.quantidade < models.Produto.estoque_minimo)
    )
    if empresa_id:
        q = q.filter(models.EstoqueSaldo.empresa_id == empresa_id)

    return [{
        "produto_id": p.id, "produto_codigo": p.codigo, "produto_descricao": p.descricao,
        "empresa_id": e.id, "empresa_nome": e.nome_fantasia or e.razao_social,
        "quantidade_atual": float(s.quantidade), "estoque_minimo": float(p.estoque_minimo or 0),
        "falta": float(p.estoque_minimo or 0) - float(s.quantidade),
    } for s, p, e in q.all()]


# ---------------------------------------------------------------------
# Curva ABC — classifica produtos pelo valor total em estoque
# (regra clássica: A = até 80% do valor acumulado, B = até 95%, C = resto)
# ---------------------------------------------------------------------
@router.get("/curva-abc")
def curva_abc(empresa_id: int | None = None, db: Session = Depends(get_db)):
    q = (
        db.query(
            models.Produto.id, models.Produto.codigo, models.Produto.descricao,
            func.coalesce(func.sum(models.EstoqueSaldo.quantidade * models.EstoqueSaldo.valor_medio), 0).label("valor_total"),
        )
        .join(models.EstoqueSaldo, models.EstoqueSaldo.produto_id == models.Produto.id)
    )
    if empresa_id:
        q = q.filter(models.EstoqueSaldo.empresa_id == empresa_id)
    q = q.group_by(models.Produto.id, models.Produto.codigo, models.Produto.descricao)
    q = q.having(func.sum(models.EstoqueSaldo.quantidade * models.EstoqueSaldo.valor_medio) > 0)

    linhas = sorted(
        [{"produto_id": r.id, "codigo": r.codigo, "descricao": r.descricao, "valor_total": float(r.valor_total)} for r in q.all()],
        key=lambda x: x["valor_total"], reverse=True,
    )

    valor_geral = sum(l["valor_total"] for l in linhas) or 1
    acumulado = 0.0
    for linha in linhas:
        acumulado += linha["valor_total"]
        pct_acumulado = acumulado / valor_geral * 100
        linha["percentual_individual"] = linha["valor_total"] / valor_geral * 100
        linha["percentual_acumulado"] = pct_acumulado
        linha["classe"] = "A" if pct_acumulado <= 80 else ("B" if pct_acumulado <= 95 else "C")

    # Persiste a classificação no cadastro do produto para reuso em outros módulos
    for linha in linhas:
        produto = db.get(models.Produto, linha["produto_id"])
        if produto:
            produto.curva_abc = linha["classe"]
    db.commit()

    resumo = {
        "A": sum(1 for l in linhas if l["classe"] == "A"),
        "B": sum(1 for l in linhas if l["classe"] == "B"),
        "C": sum(1 for l in linhas if l["classe"] == "C"),
    }
    return {"resumo": resumo, "itens": linhas}


# ---------------------------------------------------------------------
# Giro de estoque e Cobertura (dias) — baseado nas saídas do kardex
# giro = quantidade saída no período / saldo médio
# cobertura (dias) = saldo atual / consumo médio diário
# ---------------------------------------------------------------------
@router.get("/giro-cobertura")
def giro_cobertura(empresa_id: int | None = None, dias: int = 30, db: Session = Depends(get_db)):
    data_inicio = date.today() - timedelta(days=dias)

    saidas_q = (
        db.query(
            models.EstoqueMovimento.produto_id,
            func.sum(models.EstoqueMovimento.quantidade).label("qtd_saida"),
        )
        .join(models.TipoOperacao, models.TipoOperacao.id == models.EstoqueMovimento.tipo_operacao_id)
        .filter(models.TipoOperacao.natureza == "SAIDA")
        .filter(models.EstoqueMovimento.criado_em >= data_inicio)
    )
    if empresa_id:
        saidas_q = saidas_q.filter(models.EstoqueMovimento.empresa_id == empresa_id)
    saidas_q = saidas_q.group_by(models.EstoqueMovimento.produto_id)
    saidas_por_produto = {r.produto_id: float(r.qtd_saida) for r in saidas_q.all()}

    saldo_q = db.query(models.EstoqueSaldo, models.Produto).join(models.Produto, models.Produto.id == models.EstoqueSaldo.produto_id)
    if empresa_id:
        saldo_q = saldo_q.filter(models.EstoqueSaldo.empresa_id == empresa_id)

    resultado = []
    for s, p in saldo_q.all():
        qtd_saida = saidas_por_produto.get(p.id, 0)
        saldo_atual = float(s.quantidade)
        consumo_medio_diario = qtd_saida / dias if dias else 0
        giro = (qtd_saida / saldo_atual) if saldo_atual > 0 else 0
        cobertura_dias = (saldo_atual / consumo_medio_diario) if consumo_medio_diario > 0 else None

        resultado.append({
            "produto_id": p.id, "codigo": p.codigo, "descricao": p.descricao,
            "saldo_atual": saldo_atual,
            "saida_periodo": qtd_saida,
            "giro_periodo": round(giro, 2),
            "cobertura_dias": round(cobertura_dias, 1) if cobertura_dias is not None else None,
            "sem_movimento": qtd_saida == 0,
        })

    resultado.sort(key=lambda x: x["giro_periodo"], reverse=True)
    return {"periodo_dias": dias, "itens": resultado}


# ---------------------------------------------------------------------
# Kardex — extrato de movimentações
# ---------------------------------------------------------------------
@router.get("/kardex")
def kardex(produto_id: int | None = None, empresa_id: int | None = None,
           categoria_operacao: str | None = None, skip: int = 0, limit: int = 200,
           db: Session = Depends(get_db)):
    q = (
        db.query(models.EstoqueMovimento, models.Produto, models.TipoOperacao)
        .join(models.Produto, models.Produto.id == models.EstoqueMovimento.produto_id)
        .join(models.TipoOperacao, models.TipoOperacao.id == models.EstoqueMovimento.tipo_operacao_id)
    )
    if produto_id:
        q = q.filter(models.EstoqueMovimento.produto_id == produto_id)
    if empresa_id:
        q = q.filter(models.EstoqueMovimento.empresa_id == empresa_id)
    if categoria_operacao:
        q = q.filter(models.TipoOperacao.categoria == categoria_operacao)

    q = q.order_by(models.EstoqueMovimento.criado_em.desc()).offset(skip).limit(limit)

    return [{
        "id": m.id, "data": m.criado_em, "produto_codigo": p.codigo, "produto_descricao": p.descricao,
        "tipo_operacao": t.descricao, "categoria": t.categoria, "natureza": t.natureza,
        "documento_origem": m.documento_origem, "quantidade": float(m.quantidade),
        "valor_unitario": float(m.valor_unitario), "saldo_apos": float(m.saldo_apos) if m.saldo_apos is not None else None,
    } for m, p, t in q.all()]


# ---------------------------------------------------------------------
# Ajuste manual de estoque (usado por Perdas, Avarias, Consumo e Inventário
# até que cada um desses módulos tenha tela própria — todos usam este mesmo
# mecanismo de baixa/entrada via tipo_operacao)
# ---------------------------------------------------------------------
@router.post("/ajuste")
def ajuste_manual(
    empresa_id: int, produto_id: int, tipo_operacao_id: int, quantidade: float,
    documento_origem: str = "", db: Session = Depends(get_db),
):
    produto = db.get(models.Produto, produto_id)
    tipo = db.get(models.TipoOperacao, tipo_operacao_id)
    if not produto or not tipo:
        raise HTTPException(404, "Produto ou tipo de operação não encontrado")

    verificar_produto_congelado(db, empresa_id, produto_id)

    saldo_row = (
        db.query(models.EstoqueSaldo)
        .filter_by(empresa_id=empresa_id, produto_id=produto_id)
        .first()
    )
    if not saldo_row:
        saldo_row = models.EstoqueSaldo(empresa_id=empresa_id, produto_id=produto_id, quantidade=0, valor_medio=produto.preco_custo or 0)
        db.add(saldo_row)
        db.flush()

    if tipo.natureza == "SAIDA":
        if float(saldo_row.quantidade) < quantidade:
            raise HTTPException(400, f"Saldo insuficiente. Disponível: {saldo_row.quantidade}")
        saldo_row.quantidade = float(saldo_row.quantidade) - quantidade
    else:
        saldo_row.quantidade = float(saldo_row.quantidade) + quantidade

    db.add(models.EstoqueMovimento(
        empresa_id=empresa_id, produto_id=produto_id, tipo_operacao_id=tipo_operacao_id,
        documento_origem=documento_origem or tipo.codigo, quantidade=quantidade,
        valor_unitario=saldo_row.valor_medio, saldo_apos=saldo_row.quantidade,
    ))
    db.commit()
    return {"ok": True, "saldo_atual": float(saldo_row.quantidade)}


# ---------------------------------------------------------------------
# Resumo (KPIs) — usado no topo da tela de Estoque
# ---------------------------------------------------------------------
@router.get("/resumo")
def resumo(empresa_id: int | None = None, db: Session = Depends(get_db)):
    q = db.query(models.EstoqueSaldo, models.Produto).join(models.Produto, models.Produto.id == models.EstoqueSaldo.produto_id)
    if empresa_id:
        q = q.filter(models.EstoqueSaldo.empresa_id == empresa_id)
    linhas = q.all()

    valor_total = sum(float(s.quantidade) * float(s.valor_medio) for s, p in linhas)
    qtd_skus = len({p.id for s, p in linhas if float(s.quantidade) > 0})
    abaixo_minimo = sum(1 for s, p in linhas if float(s.quantidade) < float(p.estoque_minimo or 0))
    zerados = sum(1 for s, p in linhas if float(s.quantidade) <= 0)

    return {
        "valor_total_estoque": valor_total,
        "skus_com_saldo": qtd_skus,
        "produtos_abaixo_minimo": abaixo_minimo,
        "produtos_zerados": zerados,
    }
