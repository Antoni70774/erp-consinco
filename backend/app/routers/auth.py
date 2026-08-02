from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas, security
from ..database import get_db

router = APIRouter(prefix="/api/auth", tags=["Autenticação"])


@router.post("/login", response_model=schemas.Token)
def login(payload: schemas.LoginRequest, db: Session = Depends(get_db)):
    usuario = db.query(models.Usuario).filter(models.Usuario.login == payload.login).first()
    if not usuario or not security.verificar_senha(payload.senha, usuario.senha_hash):
        raise HTTPException(status_code=401, detail="Login ou senha inválidos")
    if not usuario.ativo:
        raise HTTPException(status_code=403, detail="Usuário inativo")

    token = security.criar_token({"sub": usuario.login, "uid": usuario.id})
    return schemas.Token(
        access_token=token,
        usuario={
            "id": usuario.id,
            "nome": usuario.nome,
            "login": usuario.login,
            "perfil_id": usuario.perfil_id,
            "empresa_id": usuario.empresa_id,
        },
    )


@router.get("/me", response_model=schemas.UsuarioOut)
def eu(usuario: models.Usuario = Depends(security.usuario_atual)):
    return usuario
