from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from .. import models, schemas, security
from ..database import get_db
from ..inventario_lock import verificar_produto_congelado

router = APIRouter(prefix="/api/compras", tags=["Compras"], dependencies=[Depends(security.usuario_atual)])


def _recalcular_totais(compra: models.Compra):
    total_produtos = sum(float(i.valor_total) for i in compra.itens)
    compra.valor_produtos = total_produtos
    compra.valor_total = (
        total_produtos
        + float(compra.valor_frete or 0)
        + float(compra.valor_icms_st or 0)
        - float(compra.valor_desconto or 0)
    )


@router.get("", response_model=list[schemas.CompraOut])
def listar(skip: int = 0, limit: int = 200, status: str | None = None, fornecedor_id: int | None = None,
           empresa_id: int | None = None, db: Session = Depends(get_db)):
    q = db.query(models.Compra).options(joinedload(models.Compra.itens))
    if status:
        q = q.filter(models.Compra.status == status)
    if fornecedor_id:
        q = q.filter(models.Compra.fornecedor_id == fornecedor_id)
    if empresa_id:
        q = q.filter(models.Compra.empresa_id == empresa_id)
    return q.order_by(models.Compra.id.desc()).offset(skip).limit(limit).all()


@router.get("/{compra_id}", response_model=schemas.CompraOut)
def obter(compra_id: int, db: Session = Depends(get_db)):
    obj = db.query(models.Compra).options(joinedload(models.Compra.itens)).get(compra_id)
    if not obj:
        raise HTTPException(404, "Pedido de compra não encontrado")
    return obj


@router.post("", response_model=schemas.CompraOut, status_code=201)
def criar(payload: schemas.CompraIn, db: Session = Depends(get_db)):
    dados = payload.model_dump(exclude={"itens"})
    compra = models.Compra(**dados)
    for item in payload.itens:
        compra.itens.append(models.CompraItem(**item.model_dump()))
    _recalcular_totais(compra)
    db.add(compra)
    db.commit()
    db.refresh(compra)
    return compra


@router.put("/{compra_id}", response_model=schemas.CompraOut)
def atualizar(compra_id: int, payload: schemas.CompraIn, db: Session = Depends(get_db)):
    compra = db.query(models.Compra).options(joinedload(models.Compra.itens)).get(compra_id)
    if not compra:
        raise HTTPException(404, "Pedido de compra não encontrado")

    dados = payload.model_dump(exclude={"itens"})
    for k, v in dados.items():
        setattr(compra, k, v)

    compra.itens.clear()
    for item in payload.itens:
        compra.itens.append(models.CompraItem(**item.model_dump()))

    _recalcular_totais(compra)
    db.commit()
    db.refresh(compra)
    return compra


@router.post("/{compra_id}/receber", response_model=schemas.CompraOut)
def receber_mercadoria(compra_id: int, db: Session = Depends(get_db)):
    """Confirma recebimento: atualiza estoque_saldo, grava kardex e muda status."""
    compra = db.query(models.Compra).options(joinedload(models.Compra.itens)).get(compra_id)
    if not compra:
        raise HTTPException(404, "Pedido de compra não encontrado")
    if compra.status == "RECEBIDO":
        raise HTTPException(400, "Pedido já recebido")

    for item in compra.itens:
        verificar_produto_congelado(db, compra.empresa_id, item.produto_id)
        item.quantidade_recebida = item.quantidade_pedida

        saldo = (
            db.query(models.EstoqueSaldo)
            .filter_by(empresa_id=compra.empresa_id, produto_id=item.produto_id)
            .first()
        )
        if not saldo:
            saldo = models.EstoqueSaldo(
                empresa_id=compra.empresa_id, produto_id=item.produto_id, quantidade=0, valor_medio=0
            )
            db.add(saldo)

        qtd_antiga = float(saldo.quantidade)
        valor_antigo = float(saldo.valor_medio)
        qtd_nova = float(item.quantidade_recebida)
        valor_novo = float(item.valor_unitario)

        qtd_total = qtd_antiga + qtd_nova
        saldo.valor_medio = (
            ((qtd_antiga * valor_antigo) + (qtd_nova * valor_novo)) / qtd_total if qtd_total else 0
        )
        saldo.quantidade = qtd_total

        db.add(models.EstoqueMovimento(
            empresa_id=compra.empresa_id,
            produto_id=item.produto_id,
            tipo_operacao_id=compra.tipo_operacao_id,
            documento_origem=compra.numero_pedido,
            quantidade=qtd_nova,
            valor_unitario=valor_novo,
            saldo_apos=qtd_total,
            usuario_id=compra.usuario_id,
        ))

    compra.status = "RECEBIDO"
    db.commit()
    db.refresh(compra)
    return compra


@router.delete("/{compra_id}", status_code=204)
def excluir(compra_id: int, db: Session = Depends(get_db)):
    compra = db.get(models.Compra, compra_id)
    if not compra:
        raise HTTPException(404, "Pedido de compra não encontrado")
    db.delete(compra)
    db.commit()
    return None
