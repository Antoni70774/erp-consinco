from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from .. import models, schemas, security
from ..database import get_db

router = APIRouter(prefix="/api/financeiro", tags=["Financeiro"], dependencies=[Depends(security.usuario_atual)])


# ---------------- Contas a Pagar ----------------
@router.get("/contas-pagar", response_model=list[schemas.ContaPagarOut])
def listar_pagar(status: str | None = None, fornecedor_id: int | None = None,
                  empresa_id: int | None = None, db: Session = Depends(get_db)):
    q = db.query(models.ContaPagar)
    if status:
        q = q.filter(models.ContaPagar.status == status)
    if fornecedor_id:
        q = q.filter(models.ContaPagar.fornecedor_id == fornecedor_id)
    if empresa_id:
        q = q.filter(models.ContaPagar.empresa_id == empresa_id)
    return q.order_by(models.ContaPagar.data_vencimento).all()


@router.post("/contas-pagar", response_model=schemas.ContaPagarOut, status_code=201)
def criar_pagar(payload: schemas.ContaPagarIn, db: Session = Depends(get_db)):
    obj = models.ContaPagar(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.post("/contas-pagar/{conta_id}/baixar", response_model=schemas.ContaPagarOut)
def baixar_pagar(conta_id: int, valor_pago: float, forma_pagamento: str = "", db: Session = Depends(get_db)):
    conta = db.get(models.ContaPagar, conta_id)
    if not conta:
        raise HTTPException(404, "Título não encontrado")
    conta.valor_pago = valor_pago
    conta.forma_pagamento = forma_pagamento or conta.forma_pagamento
    conta.data_pagamento = date.today()
    conta.status = "PAGO"
    db.commit()
    db.refresh(conta)
    return conta


@router.delete("/contas-pagar/{conta_id}", status_code=204)
def excluir_pagar(conta_id: int, db: Session = Depends(get_db)):
    obj = db.get(models.ContaPagar, conta_id)
    if not obj:
        raise HTTPException(404, "Título não encontrado")
    db.delete(obj)
    db.commit()


# ---------------- Contas a Receber ----------------
@router.get("/contas-receber", response_model=list[schemas.ContaReceberOut])
def listar_receber(status: str | None = None, cliente_id: int | None = None,
                    empresa_id: int | None = None, db: Session = Depends(get_db)):
    q = db.query(models.ContaReceber)
    if status:
        q = q.filter(models.ContaReceber.status == status)
    if cliente_id:
        q = q.filter(models.ContaReceber.cliente_id == cliente_id)
    if empresa_id:
        q = q.filter(models.ContaReceber.empresa_id == empresa_id)
    return q.order_by(models.ContaReceber.data_vencimento).all()


@router.post("/contas-receber", response_model=schemas.ContaReceberOut, status_code=201)
def criar_receber(payload: schemas.ContaReceberIn, db: Session = Depends(get_db)):
    obj = models.ContaReceber(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.post("/contas-receber/{conta_id}/baixar", response_model=schemas.ContaReceberOut)
def baixar_receber(conta_id: int, valor_recebido: float, forma_recebimento: str = "", db: Session = Depends(get_db)):
    conta = db.get(models.ContaReceber, conta_id)
    if not conta:
        raise HTTPException(404, "Título não encontrado")
    conta.valor_recebido = valor_recebido
    conta.forma_recebimento = forma_recebimento or conta.forma_recebimento
    conta.data_recebimento = date.today()
    conta.status = "RECEBIDO"
    db.commit()
    db.refresh(conta)
    return conta


@router.delete("/contas-receber/{conta_id}", status_code=204)
def excluir_receber(conta_id: int, db: Session = Depends(get_db)):
    obj = db.get(models.ContaReceber, conta_id)
    if not obj:
        raise HTTPException(404, "Título não encontrado")
    db.delete(obj)
    db.commit()


# ---------------- Indicadores ----------------
@router.get("/resumo")
def resumo(db: Session = Depends(get_db)):
    hoje = date.today()

    def soma(model, status_list, extra_filter=None):
        q = db.query(func.coalesce(func.sum(model.valor_original), 0)).filter(model.status.in_(status_list))
        if extra_filter is not None:
            q = q.filter(extra_filter)
        return float(q.scalar() or 0)

    a_pagar_aberto = soma(models.ContaPagar, ["ABERTO"])
    a_pagar_atrasado = soma(models.ContaPagar, ["ABERTO"], models.ContaPagar.data_vencimento < hoje)
    a_receber_aberto = soma(models.ContaReceber, ["ABERTO"])
    a_receber_atrasado = soma(models.ContaReceber, ["ABERTO"], models.ContaReceber.data_vencimento < hoje)

    return {
        "a_pagar_em_aberto": a_pagar_aberto,
        "a_pagar_atrasado": a_pagar_atrasado,
        "a_receber_em_aberto": a_receber_aberto,
        "a_receber_atrasado": a_receber_atrasado,
        "saldo_projetado": a_receber_aberto - a_pagar_aberto,
    }
