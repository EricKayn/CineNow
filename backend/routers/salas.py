from fastapi import APIRouter, HTTPException
from bson import ObjectId
from bson.errors import InvalidId

from database.conexion import db, serializar_documento

router = APIRouter(
    prefix="/salas",
    tags=["Salas"]
)


@router.get("/")
def obtener_salas():
    salas = list(db["salas"].find())

    return {
        "total": len(salas),
        "salas": serializar_documento(salas)
    }


@router.get("/{sala_id}")
def obtener_sala(sala_id: str):
    try:
        identificador = ObjectId(sala_id)
    except InvalidId:
        raise HTTPException(
            status_code=400,
            detail="El ID de la sala no es válido."
        )

    sala = db["salas"].find_one({
        "_id": identificador
    })

    if not sala:
        raise HTTPException(
            status_code=404,
            detail="Sala no encontrada."
        )

    return serializar_documento(sala)


@router.get("/cine/{cine_id}")
def obtener_salas_por_cine(cine_id: str):
    try:
        identificador = ObjectId(cine_id)
    except InvalidId:
        raise HTTPException(
            status_code=400,
            detail="El ID del cine no es válido."
        )

    salas = list(
        db["salas"].find({
            "cine_id": identificador
        })
    )

    return {
        "total": len(salas),
        "salas": serializar_documento(salas)
    }