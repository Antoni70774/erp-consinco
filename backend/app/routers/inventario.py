from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from .. import models, schemas, security
from ..database import get_db

router = APIRouter(prefix="/api/inventario", tags=["Inventário"], dependencies=[Depends(security.usuario_atual)])


@router.get("", response_model=list[schemas.InventarioOut])
def listar(empresa_id: int | None = None, status: str | None = None, db: Session = Depends(get_db)):
    q = db.query(models.Inventario).options(joinedload(models.Inventario.itens))
    if empresa_id:
        q = q.filter(models.Inventario.empresa_id == empresa_id)
    if status:
        q = q.filter(models.Inventario.status == status)
    return q.order_by(models.Inventario.id.desc()).all()


@router.get("/{inventario_id}", response_model=schemas.InventarioOut)
def obter(inventario_id: int, db: Session = Depends(get_db)):
    inv = db.query(models.Inventario).options(joinedload(models.Inventario.itens)).get(inventario_id)
    if not inv:
        raise HTTPException(404, "Inventário não encontrado")
    return inv


@router.post("", response_model=schemas.InventarioOut, status_code=201)
def abrir(payload: schemas.InventarioAbrirIn, usuario: models.Usuario = Depends(security.usuario_atual), db: Session = Depends(get_db)):
    """
    Abertura por PRODUTO (lista específica), SEÇÃO (categoria_id) ou GERAL
    (todos os produtos ativos da empresa). Congela o saldo do sistema no
    momento da abertura como referência (quantidade_sistema).
    """
    query_produtos = db.query(models.Produto).filter(models.Produto.ativo.is_(True))

    if payload.tipo_abertura == "PRODUTO":
        if not payload.produto_ids:
            raise HTTPException(400, "Informe ao menos um produto para abertura por produto.")
        query_produtos = query_produtos.filter(models.Produto.id.in_(payload.produto_ids))
    elif payload.tipo_abertura == "SECAO":
        if not payload.categoria_id:
            raise HTTPException(400, "Informe a categoria (seção) para esse tipo de abertura.")
        query_produtos = query_produtos.filter(models.Produto.categoria_id == payload.categoria_id)
    # GERAL: usa todos os produtos ativos, sem filtro adicional

    produtos = query_produtos.all()
    if not produtos:
        raise HTTPException(400, "Nenhum produto encontrado para os critérios informados.")

    inv = models.Inventario(
        empresa_id=payload.empresa_id,
        descricao=payload.descricao,
        tipo_abertura=payload.tipo_abertura,
        categoria_id=payload.categoria_id,
        tolerancia_critica_pct=payload.tolerancia_critica_pct,
        usuario_abertura_id=usuario.id,
        observacao=payload.observacao,
        status="ABERTO",
    )
    db.add(inv)
    db.flush()

    for produto in produtos:
        saldo = (
            db.query(models.EstoqueSaldo)
            .filter_by(empresa_id=payload.empresa_id, produto_id=produto.id)
            .first()
        )
        qtd_sistema = float(saldo.quantidade) if saldo else 0
        valor_unit = float(saldo.valor_medio) if saldo else float(produto.preco_custo or 0)
        inv.itens.append(models.InventarioItem(
            produto_id=produto.id, quantidade_sistema=qtd_sistema, valor_unitario=valor_unit,
        ))

    db.commit()
    db.refresh(inv)
    return inv


@router.post("/{inventario_id}/congelar", response_model=schemas.InventarioOut)
def congelar(inventario_id: int, db: Session = Depends(get_db)):
    inv = db.get(models.Inventario, inventario_id)
    if not inv:
        raise HTTPException(404, "Inventário não encontrado")
    if inv.status not in ("ABERTO",):
        raise HTTPException(400, f"Só é possível congelar um inventário em status ABERTO (atual: {inv.status}).")
    inv.status = "CONGELADO"
    inv.data_congelamento = datetime.utcnow()
    db.commit()
    db.refresh(inv)
    return inv


@router.post("/{inventario_id}/descongelar", response_model=schemas.InventarioOut)
def descongelar(inventario_id: int, db: Session = Depends(get_db)):
    inv = db.get(models.Inventario, inventario_id)
    if not inv:
        raise HTTPException(404, "Inventário não encontrado")
    if inv.status != "CONGELADO":
        raise HTTPException(400, "Este inventário não está congelado.")
    inv.status = "ABERTO"
    inv.data_congelamento = None
    db.commit()
    db.refresh(inv)
    return inv


@router.put("/{inventario_id}/itens/{item_id}/contagem", response_model=schemas.InventarioItemOut)
def registrar_contagem(inventario_id: int, item_id: int, payload: schemas.InventarioContagemIn, db: Session = Depends(get_db)):
    inv = db.get(models.Inventario, inventario_id)
    item = db.get(models.InventarioItem, item_id)
    if not inv or not item or item.inventario_id != inventario_id:
        raise HTTPException(404, "Item de inventário não encontrado")
    if inv.status == "FECHADO":
        raise HTTPException(400, "Inventário já fechado, não é possível alterar contagem.")

    item.quantidade_contada = payload.quantidade_contada
    item.diferenca = float(payload.quantidade_contada) - float(item.quantidade_sistema)
    item.valor_diferenca = item.diferenca * float(item.valor_unitario or 0)
    item.contado_em = datetime.utcnow()

    # Crítica: divergência percentual acima da tolerância definida no inventário
    base = float(item.quantidade_sistema) or 1
    divergencia_pct = abs(item.diferenca) / base * 100
    tolerancia = float(inv.tolerancia_critica_pct or 5)
    if float(item.quantidade_sistema) == 0 and float(payload.quantidade_contada) > 0:
        item.critica = True
        item.critica_motivo = "Produto sem saldo no sistema, mas contado fisicamente."
    elif divergencia_pct > tolerancia:
        item.critica = True
        item.critica_motivo = f"Divergência de {divergencia_pct:.1f}% (tolerância: {tolerancia:.0f}%)."
    else:
        item.critica = False
        item.critica_motivo = None

    db.commit()
    db.refresh(item)
    return item


@router.get("/{inventario_id}/criticas", response_model=list[schemas.InventarioItemOut])
def listar_criticas(inventario_id: int, db: Session = Depends(get_db)):
    return (
        db.query(models.InventarioItem)
        .filter(models.InventarioItem.inventario_id == inventario_id, models.InventarioItem.critica.is_(True))
        .all()
    )


@router.post("/{inventario_id}/fechar", response_model=schemas.InventarioOut)
def fechar(inventario_id: int, ignorar_criticas: bool = False,
           usuario: models.Usuario = Depends(security.usuario_atual), db: Session = Depends(get_db)):
    """
    Fecha o inventário: para cada item com diferença, gera um movimento de
    ajuste (sobra ou falta) usando os tipos de operação INV-A / INV-F,
    atualiza o saldo consolidado e o campo estoque_atual do produto.
    """
    inv = db.query(models.Inventario).options(joinedload(models.Inventario.itens)).get(inventario_id)
    if not inv:
        raise HTTPException(404, "Inventário não encontrado")
    if inv.status == "FECHADO":
        raise HTTPException(400, "Inventário já está fechado.")

    pendentes = [i for i in inv.itens if i.quantidade_contada is None]
    if pendentes:
        raise HTTPException(400, f"Existem {len(pendentes)} item(ns) sem contagem registrada.")

    criticas_abertas = [i for i in inv.itens if i.critica]
    if criticas_abertas and not ignorar_criticas:
        raise HTTPException(
            409,
            f"Existem {len(criticas_abertas)} item(ns) com crítica de divergência. "
            f"Revise-os ou feche com ignorar_criticas=true para prosseguir mesmo assim.",
        )

    tipo_sobra = db.query(models.TipoOperacao).filter_by(codigo="INV-A").first()
    tipo_falta = db.query(models.TipoOperacao).filter_by(codigo="INV-F").first()
    if not tipo_sobra or not tipo_falta:
        raise HTTPException(500, "Tipos de operação de ajuste de inventário (INV-A/INV-F) não encontrados. Rode o seed novamente.")

    for item in inv.itens:
        if item.diferenca and float(item.diferenca) != 0:
            saldo = (
                db.query(models.EstoqueSaldo)
                .filter_by(empresa_id=inv.empresa_id, produto_id=item.produto_id)
                .first()
            )
            if not saldo:
                saldo = models.EstoqueSaldo(empresa_id=inv.empresa_id, produto_id=item.produto_id, quantidade=0, valor_medio=item.valor_unitario or 0)
                db.add(saldo)
                db.flush()

            tipo = tipo_sobra if item.diferenca > 0 else tipo_falta
            saldo.quantidade = float(item.quantidade_contada)  # contagem física passa a ser a verdade

            db.add(models.EstoqueMovimento(
                empresa_id=inv.empresa_id, produto_id=item.produto_id, tipo_operacao_id=tipo.id,
                documento_origem=f"INV-{inv.id}", quantidade=abs(float(item.diferenca)),
                valor_unitario=item.valor_unitario or 0, saldo_apos=saldo.quantidade,
                usuario_id=usuario.id,
            ))
            item.ajuste_aplicado = True

            produto = db.get(models.Produto, item.produto_id)
            if produto:
                produto.estoque_atual = saldo.quantidade

    inv.status = "FECHADO"
    inv.data_fechamento = datetime.utcnow()
    inv.usuario_fechamento_id = usuario.id
    db.commit()
    db.refresh(inv)
    return inv


@router.delete("/{inventario_id}", status_code=204)
def cancelar(inventario_id: int, db: Session = Depends(get_db)):
    inv = db.get(models.Inventario, inventario_id)
    if not inv:
        raise HTTPException(404, "Inventário não encontrado")
    if inv.status == "FECHADO":
        raise HTTPException(400, "Não é possível cancelar um inventário já fechado.")
    db.delete(inv)
    db.commit()
    return None
