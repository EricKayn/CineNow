import os
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, EmailStr
from passlib.context import CryptContext
from jose import jwt, JWTError

from database.conexion import db, serializar_documento

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

SECRET_KEY = os.getenv("SECRET_KEY")

if not SECRET_KEY:
    raise RuntimeError("Falta configurar SECRET_KEY en el archivo .env")
ALGORITHM = "HS256"
TOKEN_MINUTES = 60 * 24


class UsuarioRegistro(BaseModel):
    nombre: str = Field(min_length=2, max_length=80)
    correo: EmailStr
    password: str = Field(min_length=8, max_length=72)


class UsuarioLogin(BaseModel):
    correo: EmailStr
    password: str


def crear_token(usuario_id: str):
    ahora = datetime.now(timezone.utc)
    payload = {
        "sub": usuario_id,
        "iat": ahora,
        "exp": ahora + timedelta(minutes=TOKEN_MINUTES)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def usuario_actual(
    credenciales: HTTPAuthorizationCredentials = Depends(security)
):
    try:
        payload = jwt.decode(
            credenciales.credentials,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )
        usuario_id = payload.get("sub")
        if not usuario_id:
            raise HTTPException(401, "Token inválido.")

    except JWTError:
        raise HTTPException(401, "Token inválido o expirado.")

    usuario = db["usuarios"].find_one({"_id": __import__(
        "bson"
    ).ObjectId(usuario_id)})

    if not usuario:
        raise HTTPException(401, "Usuario no encontrado.")

    return usuario


@router.post("/registro", status_code=201)
def registrar_usuario(datos: UsuarioRegistro):
    correo = datos.correo.lower()

    if db["usuarios"].find_one({"correo": correo}):
        raise HTTPException(409, "Ese correo ya está registrado.")

    usuario = {
        "nombre": datos.nombre.strip(),
        "correo": correo,
        "password": pwd_context.hash(datos.password),
        "rol": "cliente",
        "estado": "activo",
        "creado_en": datetime.now(timezone.utc)
    }

    resultado = db["usuarios"].insert_one(usuario)
    usuario["_id"] = resultado.inserted_id

    return {
        "mensaje": "Cuenta creada correctamente.",
        "usuario": {
            "id": str(usuario["_id"]),
            "nombre": usuario["nombre"],
            "correo": usuario["correo"]
        }
    }


@router.post("/login")
def iniciar_sesion(datos: UsuarioLogin):
    usuario = db["usuarios"].find_one({
        "correo": datos.correo.lower()
    })

    if (
        not usuario
        or not pwd_context.verify(
            datos.password,
            usuario.get("password", "")
        )
    ):
        raise HTTPException(401, "Correo o contraseña incorrectos.")

    if usuario.get("estado") != "activo":
        raise HTTPException(403, "La cuenta no está activa.")

    token = crear_token(str(usuario["_id"]))

    return {
        "mensaje": "Inicio de sesión exitoso.",
        "access_token": token,
        "token_type": "bearer",
        "usuario": {
            "id": str(usuario["_id"]),
            "nombre": usuario["nombre"],
            "correo": usuario["correo"],
            "rol": usuario.get("rol", "cliente")
        }
    }


@router.get("/perfil")
def obtener_perfil(usuario: dict = Depends(usuario_actual)):
    return {
        "usuario": {
            "id": str(usuario["_id"]),
            "nombre": usuario["nombre"],
            "correo": usuario["correo"],
            "rol": usuario.get("rol", "cliente")
        }
    }