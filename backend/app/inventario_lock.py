from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from .. import models

def verificar_produto_congelado(
    db: Session,
    empresa_id: int,
    produto_id: int,
    permitir_operacao_em_inventario_id: int | None = None,
):
    """
    Verifica se o produto está bloqueado por um inventário com status CONGELADO.
    Se estiver, lança HTTPException 409 com mensagem explicativa.

    Parâmetros:
    - db: Session SQLAlchemy
    - empresa_id: id da empresa onde a movimentação seria feita
    - produto_id: id do produto a ser movimentado
    - permitir_operacao_em_inventario_id: opcional; id do inventário que originou
      a operação (quando a operação faz parte do próprio fluxo de fechamento),
      nesse caso a verificação ignora esse inventário específico.

    Uso:
        verificar_produto_congelado(db, empresa_id, produto_id)
    """
    # Subquery eficiente que retorna o id do inventário congelado que contém o produto
    q = (
        db.query(models.InventarioItem.inventario_id)
        .join(models.Inventario, models.Inventario.id == models.InventarioItem.inventario_id)
        .filter(models.Inventario.empresa_id == empresa_id)
        .filter(models.Inventario.status == "CONGELADO")
        .filter(models.InventarioItem.produto_id == produto_id)
    )

    if permitir_operacao_em_inventario_id:
        q = q.filter(models.InventarioItem.inventario_id != permitir_operacao_em_inventario_id)

    bloqueado = q.with_entities(models.InventarioItem.inventario_id).first()

    if bloqueado:
        inventario_id = bloqueado[0] if isinstance(bloqueado, tuple) else bloqueado
        raise HTTPException(
            status_code=409,
            detail=(
                f"Produto bloqueado: está sob contagem no inventário CONGELADO "
                f"#{inventario_id}. Feche ou descongele o inventário para permitir movimentações deste produto."
            ),
        )
