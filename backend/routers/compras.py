
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from bson import ObjectId

from database.conexion import db, serializar_documento
from routers.usuarios import usuario_actual



# 1. CONFIGURACIÓN


router = APIRouter(
    prefix="/compras",
    tags=["Compras"]
)

# Las fechas sin zona horaria se interpretan como
# hora local de Ciudad de México.
# Si tus fechas están guardadas en UTC, cambia
# este valor a "UTC".
ZONA_HORARIA_FUNCIONES = timezone.utc



# 2. MODELOS


class CompraCrear(BaseModel):
    funcion_id: str
    asientos: list[str] = Field(
        min_length=1,
        max_length=12
    )



# 3. FUNCIONES AUXILIARES


def convertir_object_id(valor, nombre="ID"):
    try:
        return ObjectId(valor)
    except Exception:
        raise HTTPException(
            status_code=400,
            detail=f"{nombre} inválido."
        )


def validar_fecha_funcion(funcion):
    fecha = funcion.get("fecha_hora")

    if fecha is None:
        raise HTTPException(
            status_code=400,
            detail="La función no tiene una fecha válida."
        )

    if isinstance(fecha, str):
        try:
            fecha = datetime.fromisoformat(
                fecha.replace("Z", "+00:00")
            )
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="La fecha de la función no es válida."
            )

    if not isinstance(fecha, datetime):
        raise HTTPException(
            status_code=400,
            detail="Formato de fecha no válido."
        )

    # Si la fecha no tiene zona horaria,
    # interpretarla como hora de México.
    if fecha.tzinfo is None:
        fecha = fecha.replace(
            tzinfo=ZONA_HORARIA_FUNCIONES
        )

    ahora = datetime.now(timezone.utc)

    if fecha.astimezone(timezone.utc) <= ahora:
        raise HTTPException(
            status_code=400,
            detail=(
                "Esta función ya comenzó o terminó. "
                "No puedes comprar ni pagar boletos."
            )
        )


def obtener_funcion_disponible(funcion_oid):
    funcion = db["funciones"].find_one({
        "_id": funcion_oid
    })

    if not funcion:
        raise HTTPException(
            status_code=404,
            detail="Función no encontrada."
        )

    if funcion.get("estado") != "programada":
        raise HTTPException(
            status_code=400,
            detail="Esta función no está disponible."
        )

    validar_fecha_funcion(funcion)

    return funcion



# 4. CREAR COMPRA


@router.post("/", status_code=201)
def crear_compra(
    datos: CompraCrear,
    usuario: dict = Depends(usuario_actual)
):
    funcion_oid = convertir_object_id(
        datos.funcion_id,
        "ID de función"
    )

    # Normalizar asientos
    asientos = [
        asiento.strip().upper()
        for asiento in datos.asientos
    ]

    # Validar duplicados
    if len(set(asientos)) != len(asientos):
        raise HTTPException(
            status_code=400,
            detail="No puedes seleccionar asientos repetidos."
        )

    # Validar función y fecha
    funcion = obtener_funcion_disponible(funcion_oid)

    # Buscar sala
    sala = db["salas"].find_one({
        "_id": funcion["sala_id"]
    })

    if not sala:
        raise HTTPException(
            status_code=404,
            detail="No se encontró la sala."
        )

    # Obtener dimensiones
    filas = int(
        sala.get(
            "filas",
            sala.get("numero_filas", 0)
        )
    )

    por_fila = int(
        sala.get(
            "asientos_por_fila",
            sala.get("columnas", 0)
        )
    )

    # Generar asientos válidos
    asientos_validos = {
        f"{chr(64 + fila)}{numero}"
        for fila in range(1, filas + 1)
        for numero in range(1, por_fila + 1)
    }

    # Validar existencia
    if any(
        asiento not in asientos_validos
        for asiento in asientos
    ):
        raise HTTPException(
            status_code=400,
            detail="Uno o más asientos no existen en la sala."
        )

    # Buscar asientos ocupados
    ocupados = set()

    compras_existentes = db["compras"].find({
        "funcion_id": funcion_oid,
        "estado": {
            "$in": [
                "pendiente",
                "pagada",
                "confirmada"
            ]
        }
    })

    for compra_existente in compras_existentes:
        ocupados.update(
            compra_existente.get("asientos", [])
        )

    ya_ocupados = ocupados.intersection(asientos)

    if ya_ocupados:
        raise HTTPException(
            status_code=409,
            detail={
                "mensaje": "Algunos asientos ya no están disponibles.",
                "asientos": sorted(ya_ocupados)
            }
        )

    # Calcular precio
    precio = float(funcion["precio"])

    total = round(
        precio * len(asientos),
        2
    )

    # Crear documento
    compra = {
        "usuario_id": usuario["_id"],
        "funcion_id": funcion_oid,
        "asientos": asientos,
        "cantidad": len(asientos),
        "precio_unitario": precio,
        "total": total,
        "estado": "pendiente",
        "creada_en": datetime.now(timezone.utc)
    }

    # Guardar en MongoDB
    resultado = db["compras"].insert_one(compra)

    compra["_id"] = resultado.inserted_id

    return {
        "mensaje": "Compra registrada. Está pendiente de pago.",
        "compra": serializar_documento(compra)
    }



# 5. PAGAR COMPRA (SIMULADO)


@router.post("/{compra_id}/pagar")
def pagar_compra(
    compra_id: str,
    usuario: dict = Depends(usuario_actual)
):
    compra_oid = convertir_object_id(
        compra_id,
        "ID de compra"
    )

    # Buscar compra del usuario
    compra = db["compras"].find_one({
        "_id": compra_oid,
        "usuario_id": usuario["_id"]
    })

    if not compra:
        raise HTTPException(
            status_code=404,
            detail="Compra no encontrada."
        )

    # Evitar cobrar dos veces
    if compra.get("estado") == "pagada":
        return {
            "mensaje": "Esta compra ya fue pagada.",
            "compra_id": str(compra_oid),
            "estado": "pagada"
        }

    if compra.get("estado") != "pendiente":
        raise HTTPException(
            status_code=400,
            detail="Esta compra no se puede pagar."
        )

    # Comprobar que la función aún no comience
    obtener_funcion_disponible(
        compra["funcion_id"]
    )

    # Registrar pago simulado
    ahora = datetime.now(timezone.utc)

    resultado = db["compras"].update_one(
        {
            "_id": compra_oid,
            "usuario_id": usuario["_id"],
            "estado": "pendiente"
        },
        {
            "$set": {
                "estado": "pagada",
                "pagada_en": ahora,
                "metodo_pago": "simulado",
                "evento_boletos_pendiente": True
            }
        }
    )

    if resultado.modified_count == 0:
        compra_actualizada = db["compras"].find_one({
            "_id": compra_oid
        })

        if (
            compra_actualizada
            and compra_actualizada.get("estado") == "pagada"
        ):
            return {
                "mensaje": "Esta compra ya fue pagada.",
                "compra_id": str(compra_oid),
                "estado": "pagada"
            }

        raise HTTPException(
            status_code=409,
            detail="No fue posible completar el pago."
        )

    return {
        "mensaje": "¡Pago simulado exitosamente!",
        "compra_id": str(compra_oid),
        "estado": "pagada",
        "total": compra["total"]
    }



# 6. CONSULTAR MIS COMPRAS


@router.get("/mis-compras")
def obtener_mis_compras(
    usuario: dict = Depends(usuario_actual)
):
    compras = list(
        db["compras"].find({
            "usuario_id": usuario["_id"]
        }).sort("creada_en", -1)
    )

    return {
        "total": len(compras),
        "compras": serializar_documento(compras)
    }



# 7. CONSULTAR UNA COMPRA


@router.get("/{compra_id}")
def obtener_compra(
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

    return serializar_documento(compra)
