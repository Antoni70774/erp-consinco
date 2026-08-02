"""
Fábrica de rotas CRUD. Evita reescrever GET/POST/PUT/DELETE
para cada uma das ~12 entidades de cadastro do sistema.
"""
from typing import Type
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..security import usuario_atual


def build_crud_router(
    *,
    prefix: str,
    tags: list,
    model,
    schema_in,
    schema_out,
    search_fields: list[str] | None = None,
    require_auth: bool = True,
) -> APIRouter:
    router = APIRouter(prefix=prefix, tags=tags)
    deps = [Depends(usuario_atual)] if require_auth else []

    @router.get("", response_model=list[schema_out], dependencies=deps)
    def listar(skip: int = 0, limit: int = 200, q: str | None = None, db: Session = Depends(get_db)):
        query = db.query(model)
        if q and search_fields:
            from sqlalchemy import or_
            clauses = [getattr(model, f).ilike(f"%{q}%") for f in search_fields]
            query = query.filter(or_(*clauses))
        return query.order_by(model.id.desc()).offset(skip).limit(limit).all()

    @router.get("/{item_id}", response_model=schema_out, dependencies=deps)
    def obter(item_id: int, db: Session = Depends(get_db)):
        obj = db.get(model, item_id)
        if not obj:
            raise HTTPException(404, "Registro não encontrado")
        return obj

    @router.post("", response_model=schema_out, status_code=201, dependencies=deps)
    def criar(payload: schema_in, db: Session = Depends(get_db)):
        obj = model(**payload.model_dump())
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @router.put("/{item_id}", response_model=schema_out, dependencies=deps)
    def atualizar(item_id: int, payload: schema_in, db: Session = Depends(get_db)):
        obj = db.get(model, item_id)
        if not obj:
            raise HTTPException(404, "Registro não encontrado")
        for k, v in payload.model_dump().items():
            setattr(obj, k, v)
        db.commit()
        db.refresh(obj)
        return obj

    @router.delete("/{item_id}", status_code=204, dependencies=deps)
    def excluir(item_id: int, db: Session = Depends(get_db)):
        obj = db.get(model, item_id)
        if not obj:
            raise HTTPException(404, "Registro não encontrado")
        db.delete(obj)
        db.commit()
        return None

    return router
