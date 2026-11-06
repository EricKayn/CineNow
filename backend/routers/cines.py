from fastapi import APIRouter, HTTPException
from bson import ObjectId
from bson.errors import InvalidId

from database.conexion import db, serializar_documento

router = APIRouter(
    prefix="/cines",
    tags=["Cines"]
)


@router.get("/")
def obtener_cines():
    cines = list(db["cines"].find())

    return {
        "total": len(cines),
        "cines": serializar_documento(cines)
    }


@router.get("/{cine_id}")
def obtener_cine(cine_id: str):
    try:
        identificador = ObjectId(cine_id)
    except InvalidId:
        raise HTTPException(
            status_code=400,
            detail="El ID del cine no es válido."
        )

    cine = db["cines"].find_one({
        "_id": identificador
    })

    if not cine:
        raise HTTPException(
            status_code=404,
            detail="Cine no encontrado."
        )

    return serializar_documento(cine)