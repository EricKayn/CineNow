from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from bson import ObjectId
from bson.errors import InvalidId

from database.conexion import db, serializar_documento

router = APIRouter(
    prefix="/funciones",
    tags=["Funciones"]
)


class FuncionCrear(BaseModel):
    pelicula_id: str
    cine_id: str
    sala_id: str
    fecha_hora: datetime
    formato: str = "2D"
    idioma: str = "Español"
    precio: float = Field(gt=0)


def convertir_id(valor: str, nombre: str):
    try:
        return ObjectId(valor)
    except (InvalidId, TypeError):
        raise HTTPException(
            status_code=400,
            detail=f"El ID de {nombre} no es válido."
        )


@router.get("/")
def obtener_funciones():
    funciones = list(db["funciones"].find())

    return {
        "total": len(funciones),
        "funciones": serializar_documento(funciones)
    }


@router.get("/{funcion_id}")
def obtener_funcion(funcion_id: str):
    funcion_oid = convertir_id(funcion_id, "función")

    funcion = db["funciones"].find_one({
        "_id": funcion_oid
    })

    if not funcion:
        raise HTTPException(
            status_code=404,
            detail="Función no encontrada."
        )

    return serializar_documento(funcion)


@router.post("/", status_code=201)
def crear_funcion(datos: FuncionCrear):

    pelicula_oid = convertir_id(
        datos.pelicula_id,
        "película"
    )

    cine_oid = convertir_id(
        datos.cine_id,
        "cine"
    )

    sala_oid = convertir_id(
        datos.sala_id,
        "sala"
    )

    pelicula = db["peliculas"].find_one({
        "_id": pelicula_oid
    })

    if not pelicula:
        raise HTTPException(
            status_code=404,
            detail="La película no existe."
        )

    cine = db["cines"].find_one({
        "_id": cine_oid
    })

    if not cine:
        raise HTTPException(
            status_code=404,
            detail="El cine no existe."
        )

    sala = db["salas"].find_one({
        "_id": sala_oid
    })

    if not sala:
        raise HTTPException(
            status_code=404,
            detail="La sala no existe."
        )

    # Comprobar la relación entre sala y cine.
    cine_id_sala = sala.get("cine_id")

    if isinstance(cine_id_sala, dict):
        cine_id_sala = cine_id_sala.get("$oid")

    if isinstance(cine_id_sala, ObjectId):
        cine_id_sala = str(cine_id_sala)

    if str(cine_id_sala) != str(cine_oid):
        raise HTTPException(
            status_code=400,
            detail="La sala seleccionada no pertenece al cine indicado."
        )

    if sala.get("estado") != "activa":
        raise HTTPException(
            status_code=400,
            detail="La sala no está activa."
        )

    if cine.get("estado") != "activo":
        raise HTTPException(
            status_code=400,
            detail="El cine no está activo."
        )

    if datos.fecha_hora <= datetime.now():
        raise HTTPException(
            status_code=400,
            detail="La fecha de la función debe ser futura."
        )

    # Evitar programar dos funciones en la misma sala
    # a la misma hora.
    conflicto = db["funciones"].find_one({
        "sala_id": sala_oid,
        "fecha_hora": datos.fecha_hora,
        "estado": "programada"
    })

    if conflicto:
        raise HTTPException(
            status_code=409,
            detail="Ya existe una función programada en esa sala y horario."
        )

    funcion = {
        "pelicula_id": pelicula_oid,
        "cine_id": cine_oid,
        "sala_id": sala_oid,
        "fecha_hora": datos.fecha_hora,
        "formato": datos.formato,
        "idioma": datos.idioma,
        "precio": datos.precio,
        "estado": "programada",
        "creada_en": datetime.now(timezone.utc)
    }

    resultado = db["funciones"].insert_one(funcion)

    funcion["_id"] = resultado.inserted_id

    return {
        "mensaje": "Función creada correctamente.",
        "funcion": serializar_documento(funcion)
    }


@router.get("/pelicula/{pelicula_id}")
def funciones_por_pelicula(pelicula_id: str):

    pelicula_oid = convertir_id(
        pelicula_id,
        "película"
    )

    funciones = list(db["funciones"].find({
        "pelicula_id": pelicula_oid,
        "estado": "programada"
    }))

    return {
        "total": len(funciones),
        "funciones": serializar_documento(funciones)
    }


@router.get("/cine/{cine_id}")
def funciones_por_cine(cine_id: str):

    cine_oid = convertir_id(
        cine_id,
        "cine"
    )

    funciones = list(db["funciones"].find({
        "cine_id": cine_oid,
        "estado": "programada"
    }))

    return {
        "total": len(funciones),
        "funciones": serializar_documento(funciones)
    }