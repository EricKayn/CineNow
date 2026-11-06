from fastapi import APIRouter, HTTPException
from bson import ObjectId
from bson.errors import InvalidId

from database.conexion import db, serializar_documento

router = APIRouter(
    prefix="/peliculas",
    tags=["Películas"]
)


@router.get("/")
def obtener_peliculas():
    peliculas = list(db["peliculas"].find())

    return {
        "total": len(peliculas),
        "peliculas": serializar_documento(peliculas)
    }


@router.get("/{pelicula_id}")
def obtener_pelicula(pelicula_id: str):
    try:
        identificador = ObjectId(pelicula_id)
    except InvalidId:
        raise HTTPException(
            status_code=400,
            detail="El ID de la película no es válido."
        )

    pelicula = db["peliculas"].find_one({
        "_id": identificador
    })

    if not pelicula:
        raise HTTPException(
            status_code=404,
            detail="Película no encontrada."
        )

    return serializar_documento(pelicula)