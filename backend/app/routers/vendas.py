from datetime import date, datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from .. import models, schemas, security
from ..database import get_db
from ..inventario_lock import verificar_produto_congelado

router = APIRouter(prefix="/api/vendas", tags=["Vendas"], dependencies=[Depends(security.usuario_atual)])


# ---------------------------------------------------------------------
# CRUD básico
# ---------------------------------------------------------------------
@router.get("", response_model=list[schemas.VendaOut])
def listar(skip: int = 0, limit: int = 200, status: str | None = None, empresa_id: int | None = None,
           cliente_id: int | None = None, db: Session = Depends(get_db)):
    q = db.query(models.Venda).options(joinedload(models.Venda.itens))
    if status:
        q = q.filter(models.Venda.status == status)
    if empresa_id:
        q = q.filter(models.Venda.empresa_id == empresa_id)
    if cliente_id:
        q = q.filter(models.Venda.cliente_id == cliente_id)
    return q.order_by(models.Venda.id.desc()).offset(skip).limit(limit).all()


@router.get("/{venda_id}", response_model=schemas.VendaOut)
def obter(venda_id: int, db: Session = Depends(get_db)):
    venda = db.query(models.Venda).options(joinedload(models.Venda.itens)).get(venda_id)
    if not venda:
        raise HTTPException(404, "Venda não encontrada")
    return venda


@router.post("", response_model=schemas.VendaOut, status_code=201)
def criar(payload: schemas.VendaIn, usuario: models.Usuario = Depends(security.usuario_atual), db: Session = Depends(get_db)):
    if not payload.itens:
        raise HTTPException(400, "Informe ao menos um item na venda.")

    tipo_venda = None
    if payload.tipo_operacao_id:
        tipo_venda = db.get(models.TipoOperacao, payload.tipo_operacao_id)
    if not tipo_venda:
        tipo_venda = db.query(models.TipoOperacao).filter_by(codigo="VDA").first()
        if not tipo_venda:
            raise HTTPException(500, "Tipo de operação de Venda não encontrado. Rode o seed novamente.")

    for item in payload.itens:
        verificar_produto_congelado(db, payload.empresa_id, item.produto_id)
        saldo = db.query(models.EstoqueSaldo).filter_by(empresa_id=payload.empresa_id, produto_id=item.produto_id).first()
        disponivel = float(saldo.quantidade) if saldo else 0
        if disponivel < item.quantidade:
            produto = db.get(models.Produto, item.produto_id)
            raise HTTPException(400, f"Saldo insuficiente para {produto.descricao if produto else item.produto_id}. Disponível: {disponivel}")

    venda = models.Venda(
        numero_venda=payload.numero_venda, empresa_id=payload.empresa_id, cliente_id=payload.cliente_id,
        tipo_operacao_id=tipo_venda.id, usuario_id=usuario.id,
        data_venda=payload.data_venda or datetime.utcnow(),
        valor_desconto=payload.valor_desconto, observacao=payload.observacao,
    )
    valor_produtos = 0.0
    for item in payload.itens:
        venda.itens.append(models.VendaItem(**item.model_dump()))
        valor_produtos += item.valor_total
    venda.valor_produtos = valor_produtos
    venda.valor_total = valor_produtos - payload.valor_desconto
    db.add(venda)
    db.flush()

    for item in venda.itens:
        saldo = db.query(models.EstoqueSaldo).filter_by(empresa_id=payload.empresa_id, produto_id=item.produto_id).first()
        saldo.quantidade = float(saldo.quantidade) - float(item.quantidade)
        db.add(models.EstoqueMovimento(
            empresa_id=payload.empresa_id, produto_id=item.produto_id, tipo_operacao_id=tipo_venda.id,
            documento_origem=venda.numero_venda, quantidade=item.quantidade,
            valor_unitario=item.valor_unitario, saldo_apos=saldo.quantidade, usuario_id=usuario.id,
        ))
        produto = db.get(models.Produto, item.produto_id)
        if produto:
            produto.estoque_atual = saldo.quantidade

    if payload.gerar_financeiro and payload.cliente_id:
        db.add(models.ContaReceber(
            empresa_id=payload.empresa_id, cliente_id=payload.cliente_id, venda_id=venda.id,
            numero_documento=venda.numero_venda, valor_original=venda.valor_total,
            data_vencimento=date.today() + timedelta(days=payload.dias_vencimento),
        ))

    db.commit()
    db.refresh(venda)
    return venda


@router.post("/{venda_id}/cancelar", response_model=schemas.VendaOut)
def cancelar(venda_id: int, usuario: models.Usuario = Depends(security.usuario_atual), db: Session = Depends(get_db)):
    venda = db.query(models.Venda).options(joinedload(models.Venda.itens)).get(venda_id)
    if not venda:
        raise HTTPException(404, "Venda não encontrada")
    if venda.status == "CANCELADA":
        raise HTTPException(400, "Venda já está cancelada.")

    tipo_dev = db.query(models.TipoOperacao).filter_by(codigo="DEV-V").first()
    for item in venda.itens:
        qtd_estornar = float(item.quantidade) - float(item.quantidade_devolvida or 0)
        if qtd_estornar <= 0:
            continue
        saldo = db.query(models.EstoqueSaldo).filter_by(empresa_id=venda.empresa_id, produto_id=item.produto_id).first()
        if not saldo:
            saldo = models.EstoqueSaldo(empresa_id=venda.empresa_id, produto_id=item.produto_id, quantidade=0, valor_medio=item.valor_unitario)
            db.add(saldo)
            db.flush()
        saldo.quantidade = float(saldo.quantidade) + qtd_estornar
        db.add(models.EstoqueMovimento(
            empresa_id=venda.empresa_id, produto_id=item.produto_id, tipo_operacao_id=tipo_dev.id,
            documento_origem=venda.numero_venda, quantidade=qtd_estornar,
            valor_unitario=item.valor_unitario, saldo_apos=saldo.quantidade, usuario_id=usuario.id,
        ))
        item.quantidade_devolvida = item.quantidade

    venda.status = "CANCELADA"
    db.commit()
    db.refresh(venda)
    return venda


@router.post("/{venda_id}/devolver", response_model=schemas.VendaOut)
def devolver(venda_id: int, payload: schemas.VendaDevolucaoIn,
             usuario: models.Usuario = Depends(security.usuario_atual), db: Session = Depends(get_db)):
    venda = db.query(models.Venda).options(joinedload(models.Venda.itens)).get(venda_id)
    if not venda:
        raise HTTPException(404, "Venda não encontrada")

    tipo_dev = db.query(models.TipoOperacao).filter_by(codigo="DEV-V").first()
    if not tipo_dev:
        raise HTTPException(500, "Tipo de operação de devolução não encontrado.")

    itens_map = {i.id: i for i in venda.itens}
    for dev in payload.itens:
        item = itens_map.get(dev.item_id)
        if not item:
            raise HTTPException(404, f"Item {dev.item_id} não pertence a esta venda.")
        disponivel_para_devolver = float(item.quantidade) - float(item.quantidade_devolvida or 0)
        if dev.quantidade > disponivel_para_devolver:
            raise HTTPException(400, f"Quantidade a devolver maior que a disponível ({disponivel_para_devolver}) para o item {item.id}.")

        saldo = db.query(models.EstoqueSaldo).filter_by(empresa_id=venda.empresa_id, produto_id=item.produto_id).first()
        if not saldo:
            saldo = models.EstoqueSaldo(empresa_id=venda.empresa_id, produto_id=item.produto_id, quantidade=0, valor_medio=item.valor_unitario)
            db.add(saldo)
            db.flush()
        saldo.quantidade = float(saldo.quantidade) + dev.quantidade
        item.quantidade_devolvida = float(item.quantidade_devolvida or 0) + dev.quantidade

        db.add(models.EstoqueMovimento(
            empresa_id=venda.empresa_id, produto_id=item.produto_id, tipo_operacao_id=tipo_dev.id,
            documento_origem=venda.numero_venda, motivo=payload.motivo,
            quantidade=dev.quantidade, valor_unitario=item.valor_unitario,
            saldo_apos=saldo.quantidade, usuario_id=usuario.id,
        ))
        produto = db.get(models.Produto, item.produto_id)
        if produto:
            produto.estoque_atual = saldo.quantidade

    total_pedido = sum(float(i.quantidade) for i in venda.itens)
    total_devolvido = sum(float(i.quantidade_devolvida or 0) for i in venda.itens)
    venda.status = "DEVOLVIDA_TOTAL" if total_devolvido >= total_pedido else "DEVOLVIDA_PARCIAL"

    db.commit()
    db.refresh(venda)
    return venda


# ---------------------------------------------------------------------
# Análises
# ---------------------------------------------------------------------
@router.get("/analise/resumo")
def resumo(empresa_id: int | None = None, db: Session = Depends(get_db)):
    hoje = date.today()
    q = db.query(models.Venda).filter(models.Venda.status.in_(["CONCLUIDA", "DEVOLVIDA_PARCIAL"]))
    if empresa_id:
        q = q.filter(models.Venda.empresa_id == empresa_id)

    vendas_mes = q.filter(
        func.extract("month", models.Venda.data_venda) == hoje.month,
        func.extract("year", models.Venda.data_venda) == hoje.year,
    ).all()

    valor_mes = sum(float(v.valor_total) for v in vendas_mes)
    qtd_vendas_mes = len(vendas_mes)
    ticket_medio = valor_mes / qtd_vendas_mes if qtd_vendas_mes else 0

    devolucoes_q = db.query(func.count(models.Venda.id)).filter(models.Venda.status.in_(["DEVOLVIDA_PARCIAL", "DEVOLVIDA_TOTAL"]))
    if empresa_id:
        devolucoes_q = devolucoes_q.filter(models.Venda.empresa_id == empresa_id)

    return {
        "valor_vendido_mes": valor_mes, "qtd_vendas_mes": qtd_vendas_mes,
        "ticket_medio_mes": ticket_medio, "total_devolucoes": devolucoes_q.scalar() or 0,
    }


@router.get("/analise/por-produto")
def por_produto(empresa_id: int | None = None, dias: int = 30, limit: int = 50, db: Session = Depends(get_db)):
    data_inicio = datetime.utcnow() - timedelta(days=dias)
    q = (
        db.query(
            models.Produto.id, models.Produto.codigo, models.Produto.descricao,
            func.coalesce(func.sum(models.VendaItem.quantidade), 0),
            func.coalesce(func.sum(models.VendaItem.valor_total), 0),
        )
        .join(models.VendaItem, models.VendaItem.produto_id == models.Produto.id)
        .join(models.Venda, models.Venda.id == models.VendaItem.venda_id)
        .filter(models.Venda.status.in_(["CONCLUIDA", "DEVOLVIDA_PARCIAL"]))
        .filter(models.Venda.data_venda >= data_inicio)
    )
    if empresa_id:
        q = q.filter(models.Venda.empresa_id == empresa_id)
    q = q.group_by(models.Produto.id, models.Produto.codigo, models.Produto.descricao)

    resultado = [{"produto_id": r[0], "codigo": r[1], "descricao": r[2], "quantidade": float(r[3]), "valor_total": float(r[4])} for r in q.all()]
    resultado.sort(key=lambda x: x["valor_total"], reverse=True)
    return resultado[:limit]


@router.get("/analise/comparativo-mensal")
def comparativo_mensal(empresa_id: int | None = None, meses: int = 12, db: Session = Depends(get_db)):
    data_inicio = date.today().replace(day=1) - timedelta(days=31 * meses)
    q = (
        db.query(
            func.date_trunc("month", models.Venda.data_venda).label("mes"),
            func.coalesce(func.sum(models.Venda.valor_total), 0),
            func.count(models.Venda.id),
        )
        .filter(models.Venda.status.in_(["CONCLUIDA", "DEVOLVIDA_PARCIAL"]))
        .filter(models.Venda.data_venda >= data_inicio)
    )
    if empresa_id:
        q = q.filter(models.Venda.empresa_id == empresa_id)
    q = q.group_by("mes").order_by("mes")
    return [{"mes": r[0].strftime("%Y-%m"), "valor_total": float(r[1]), "qtd_vendas": r[2]} for r in q.all()]


@router.get("/analise/comparativo-anual")
def comparativo_anual(empresa_id: int | None = None, db: Session = Depends(get_db)):
    q = (
        db.query(
            func.extract("year", models.Venda.data_venda).label("ano"),
            func.coalesce(func.sum(models.Venda.valor_total), 0),
            func.count(models.Venda.id),
        )
        .filter(models.Venda.status.in_(["CONCLUIDA", "DEVOLVIDA_PARCIAL"]))
    )
    if empresa_id:
        q = q.filter(models.Venda.empresa_id == empresa_id)
    q = q.group_by("ano").order_by("ano")
    return [{"ano": int(r[0]), "valor_total": float(r[1]), "qtd_vendas": r[2]} for r in q.all()]


@router.get("/analise/por-empresa")
def por_empresa(dias: int = 30, db: Session = Depends(get_db)):
    data_inicio = datetime.utcnow() - timedelta(days=dias)
    q = (
        db.query(
            models.Empresa.id, models.Empresa.nome_fantasia, models.Empresa.razao_social,
            func.coalesce(func.sum(models.Venda.valor_total), 0), func.count(models.Venda.id),
        )
        .join(models.Venda, models.Venda.empresa_id == models.Empresa.id)
        .filter(models.Venda.status.in_(["CONCLUIDA", "DEVOLVIDA_PARCIAL"]))
        .filter(models.Venda.data_venda >= data_inicio)
        .group_by(models.Empresa.id, models.Empresa.nome_fantasia, models.Empresa.razao_social)
    )
    return [{"empresa_id": r[0], "empresa_nome": r[1] or r[2], "valor_total": float(r[3]), "qtd_vendas": r[4]} for r in q.all()]


@router.get("/analise/devolucoes")
def devolucoes(empresa_id: int | None = None, db: Session = Depends(get_db)):
    q = db.query(models.Venda).options(joinedload(models.Venda.itens)).filter(models.Venda.status.in_(["DEVOLVIDA_PARCIAL", "DEVOLVIDA_TOTAL"]))
    if empresa_id:
        q = q.filter(models.Venda.empresa_id == empresa_id)

    resultado = []
    for v in q.order_by(models.Venda.id.desc()).all():
        valor_devolvido = sum(float(i.quantidade_devolvida or 0) * float(i.valor_unitario) for i in v.itens)
        resultado.append({
            "venda_id": v.id, "numero_venda": v.numero_venda, "status": v.status,
            "data_venda": v.data_venda, "valor_total_venda": float(v.valor_total),
            "valor_devolvido": valor_devolvido,
        })
    return resultado
