
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Depends
from bson import ObjectId
from pymongo.errors import DuplicateKeyError

from database.conexion import db, serializar_documento
from routers.usuarios import usuario_actual



# 1. CONFIGURACIÓN


router = APIRouter(
    prefix="/boletos",
    tags=["Boletos"]
)



# 2. FUNCIONES AUXILIARES


def convertir_object_id(valor, nombre="ID"):
    try:
        return ObjectId(valor)
    except Exception:
        raise HTTPException(
            status_code=400,
            detail=f"{nombre} inválido."
        )


def buscar_documento(coleccion, valor):
    """
    Busca un documento por su identificador.
    Acepta ObjectId o texto.
    """
    if valor is None:
        return None

    if isinstance(valor, ObjectId):
        identificador = valor
    else:
        try:
            identificador = ObjectId(str(valor))
        except Exception:
            identificador = valor

    return db[coleccion].find_one({
        "_id": identificador
    })


def enriquecer_boleto(boleto):
    """
    Agrega información de película, cine, sala
    y función sin modificar el boleto guardado.
    """
    resultado = dict(boleto)

    funcion = buscar_documento(
        "funciones",
        boleto.get("funcion_id")
    )

    if not funcion:
        return resultado

    pelicula = buscar_documento(
        "peliculas",
        funcion.get("pelicula_id")
    )

    cine = buscar_documento(
        "cines",
        funcion.get("cine_id")
    )

    sala = buscar_documento(
        "salas",
        funcion.get("sala_id")
    )

    resultado["fecha_hora"] = funcion.get("fecha_hora")
    resultado["formato"] = funcion.get("formato")
    resultado["idioma"] = funcion.get("idioma")

    resultado["pelicula"] = (
        pelicula.get("titulo", "Película no disponible")
        if pelicula
        else "Película no disponible"
    )

    resultado["cine"] = (
        cine.get("nombre", "Cine no disponible")
        if cine
        else "Cine no disponible"
    )

    resultado["sala"] = (
        sala.get("nombre", "Sala no disponible")
        if sala
        else "Sala no disponible"
    )

    return resultado


def serializar_boletos(boletos):
    return serializar_documento([
        enriquecer_boleto(boleto)
        for boleto in boletos
    ])



# 3. CONSULTAR MIS BOLETOS


@router.get("/mis-boletos")
def obtener_mis_boletos(
    usuario: dict = Depends(usuario_actual)
):
    boletos = list(
        db["boletos"].find({
            "usuario_id": usuario["_id"]
        }).sort("creado_en", -1)
    )

    return {
        "total": len(boletos),
        "boletos": serializar_boletos(boletos)
    }



# 4. CONSULTAR UN BOLETO


@router.get("/{boleto_id}")
def obtener_boleto(
    boleto_id: str,
    usuario: dict = Depends(usuario_actual)
):
    boleto_oid = convertir_object_id(
        boleto_id,
        "ID de boleto"
    )

    boleto = db["boletos"].find_one({
        "_id": boleto_oid,
        "usuario_id": usuario["_id"]
    })

    if not boleto:
        raise HTTPException(
            status_code=404,
            detail="Boleto no encontrado."
        )

    return serializar_documento(
        enriquecer_boleto(boleto)
    )



# 5. CONSULTAR BOLETOS DE UNA COMPRA


@router.post("/generar/{compra_id}", status_code=200)
def generar_boletos(
    compra_id: str,
    usuario: dict = Depends(usuario_actual)
):
    compra_oid = convertir_object_id(
        compra_id,
        "ID de compra"
    )

    compra = db["compras"].find_one({
        "_id": compra_oid,
        "usuario_id": usuario["_id"]
    })

    if not compra:
        raise HTTPException(
            status_code=404,
            detail="Compra no encontrada."
        )

    if compra.get("estado") != "pagada":
        raise HTTPException(
            status_code=400,
            detail="La compra no está pagada."
        )

    boletos = list(db["boletos"].find({
        "compra_id": compra_oid,
        "usuario_id": usuario["_id"]
    }))

    disponibles = set(compra["asientos"]).issubset(
        {boleto["asiento"] for boleto in boletos}
    )

    return {
        "mensaje": (
            "Los boletos están disponibles."
            if disponibles
            else "Tus boletos se están generando."
        ),
        "estado": (
            "disponibles"
            if disponibles
            else "procesando"
        ),
        "total": len(boletos),
        "boletos": serializar_boletos(boletos)
    }