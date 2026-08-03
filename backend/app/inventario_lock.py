"""
Trava de congelamento de estoque: enquanto um inventário estiver com
status CONGELADO, produtos que fazem parte dele não podem sofrer novas
movimentações de estoque (compra recebida, ajuste manual etc.) até o
inventário ser fechado ou descongelado — isso garante que a contagem
física não seja invalidada por uma movimentação no meio do processo.
"""
from fastapi import HTTPException
from sqlalchemy.orm import Session
from . import models


def verificar_produto_congelado(db: Session, empresa_id: int, produto_id: int):
    bloqueado = (
        db.query(models.InventarioItem)
        .join(models.Inventario, models.Inventario.id == models.InventarioItem.inventario_id)
        .filter(models.Inventario.empresa_id == empresa_id)
        .filter(models.Inventario.status == "CONGELADO")
        .filter(models.InventarioItem.produto_id == produto_id)
        .first()
    )
    if bloqueado:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Produto bloqueado: está sob contagem no inventário congelado "
                f"#{bloqueado.inventario_id}. Feche ou descongele o inventário "
                f"para movimentar este produto."
            ),
        )
