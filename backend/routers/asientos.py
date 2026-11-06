
from fastapi import APIRouter, HTTPException, Depends
from bson import ObjectId
from bson.errors import InvalidId
from pydantic import BaseModel, Field
from redis.exceptions import RedisError

from database.conexion import db, serializar_documento
from database.redis_conexion import redis_cliente
from routers.usuarios import usuario_actual



# 1. CONFIGURACIÓN


router = APIRouter(
    prefix="/asientos",
    tags=["Asientos"]
)

TIEMPO_RESERVA = 600  # 10 minutos



# 2. MODELOS


class ReservaAsientos(BaseModel):
    funcion_id: str
    asientos: list[str] = Field(min_length=1)



# 3. FUNCIONES AUXILIARES


def convertir_id(valor: str):
    try:
        return ObjectId(valor)
    except (InvalidId, TypeError):
        raise HTTPException(
            status_code=400,
            detail="Identificador no válido."
        )


def generar_codigo(fila: int, numero: int):
    letra = chr(64 + fila)
    return f"{letra}{numero}"


def obtener_distribucion(sala):
    filas = int(
        sala.get("filas", sala.get("numero_filas", 0))
    )

    por_fila = int(
        sala.get(
            "asientos_por_fila",
            sala.get("columnas", 0)
        )
    )

    if filas <= 0 or por_fila <= 0:
        raise HTTPException(
            status_code=400,
            detail=(
                "La sala no tiene una distribución "
                "de asientos configurada."
            )
        )

    return filas, por_fila


def obtener_ocupados(funcion_oid):
    ocupados = set()

    compras = db["compras"].find({
        "funcion_id": funcion_oid,
        "estado": {
            "$in": ["pagada", "confirmada"]
        }
    })

    for compra in compras:
        ocupados.update(
            str(asiento).strip().upper()
            for asiento in compra.get("asientos", [])
        )

    return ocupados


def clave_reserva(funcion_id, asiento):
    return f"reserva:{funcion_id}:{asiento}"

def liberar_reservas_propias(claves, usuario_id):
    """
    Elimina una reserva solamente si sigue
    perteneciendo al usuario indicado.
    La comprobación y eliminación son atómicas.
    """

    script = """
    for i = 1, #KEYS do
        if redis.call('GET', KEYS[i]) == ARGV[1] then
            redis.call('DEL', KEYS[i])
        end
    end
    return 1
    """

    if claves:
        redis_cliente.eval(
            script,
            len(claves),
            *claves,
            usuario_id
        )

def obtener_reservados(funcion_id, codigos):
    """
    Consulta Redis para identificar
    los asientos reservados temporalmente.
    """
    claves = [
        clave_reserva(funcion_id, codigo)
        for codigo in codigos
    ]

    try:
        valores = redis_cliente.mget(claves)
    except RedisError:
        raise HTTPException(
            status_code=503,
            detail="El servicio de reservas no está disponible."
        )

    return {
        codigo
        for codigo, valor in zip(codigos, valores)
        if valor is not None
    }


def obtener_funcion_y_sala(funcion_oid):
    funcion = db["funciones"].find_one({
        "_id": funcion_oid
    })

    if not funcion:
        raise HTTPException(
            status_code=404,
            detail="Función no encontrada."
        )

    sala = db["salas"].find_one({
        "_id": funcion["sala_id"]
    })

    if not sala:
        raise HTTPException(
            status_code=404,
            detail="Sala no encontrada."
        )

    return funcion, sala



# 4. CONSULTAR ASIENTOS DE UNA FUNCIÓN


@router.get("/funcion/{funcion_id}")
def obtener_asientos_funcion(funcion_id: str):
    funcion_oid = convertir_id(funcion_id)

    funcion, sala = obtener_funcion_y_sala(
        funcion_oid
    )

    filas, por_fila = obtener_distribucion(sala)

    codigos = [
        generar_codigo(fila, numero)
        for fila in range(1, filas + 1)
        for numero in range(1, por_fila + 1)
    ]

    ocupados = obtener_ocupados(funcion_oid)

    reservados = obtener_reservados(
        str(funcion_oid),
        codigos
    )

    asientos = []

    for fila in range(1, filas + 1):
        for numero in range(1, por_fila + 1):
            codigo = generar_codigo(fila, numero)

            if codigo in ocupados:
                estado = "ocupado"

            elif codigo in reservados:
                estado = "reservado"

            else:
                estado = "disponible"

            asientos.append({
                "codigo": codigo,
                "fila": fila,
                "numero": numero,
                "estado": estado
            })

    return {
        "funcion_id": str(funcion_oid),
        "total": len(asientos),
        "disponibles": sum(
            1 for asiento in asientos
            if asiento["estado"] == "disponible"
        ),
        "ocupados": sum(
            1 for asiento in asientos
            if asiento["estado"] == "ocupado"
        ),
        "reservados": sum(
            1 for asiento in asientos
            if asiento["estado"] == "reservado"
        ),
        "asientos": asientos
    }



# 5. RESERVAR ASIENTOS TEMPORALMENTE


@router.post("/reservar")
def reservar_asientos(
    datos: ReservaAsientos,
    usuario: dict = Depends(usuario_actual)
):
    funcion_oid = convertir_id(datos.funcion_id)

    funcion, sala = obtener_funcion_y_sala(
        funcion_oid
    )

    filas, por_fila = obtener_distribucion(sala)

    codigos_validos = {
        generar_codigo(fila, numero)
        for fila in range(1, filas + 1)
        for numero in range(1, por_fila + 1)
    }

    solicitados = datos.asientos

    if len(solicitados) != len(set(solicitados)):
        raise HTTPException(
            status_code=400,
            detail="Hay asientos repetidos en la solicitud."
        )

    for asiento in solicitados:
        if asiento not in codigos_validos:
            raise HTTPException(
                status_code=400,
                detail=f"El asiento {asiento} no existe."
            )

    ocupados = obtener_ocupados(funcion_oid)

    for asiento in solicitados:
        if asiento in ocupados:
            raise HTTPException(
                status_code=409,
                detail=f"El asiento {asiento} ya está ocupado."
            )

    usuario_id = str(usuario["_id"])
    funcion_id = str(funcion_oid)

    claves_creadas = []

    try:
        for asiento in solicitados:
            clave = clave_reserva(
                funcion_id,
                asiento
            )

            # SET NX EX crea la reserva solamente
            # si el asiento todavía no está reservado.
            reservado = redis_cliente.set(
                clave,
                usuario_id,
                nx=True,
                ex=TIEMPO_RESERVA
            )

            if not reservado:
                propietario = redis_cliente.get(clave)

                if propietario == usuario_id:
                    # La reserva ya pertenece al usuario.
                    continue

                raise HTTPException(
                    status_code=409,
                    detail=(
                        f"El asiento {asiento} está "
                        "reservado por otro usuario."
                    )
                )

            claves_creadas.append(clave)

    except (HTTPException, RedisError) as error:
        try:
            liberar_reservas_propias(
                claves_creadas,
                usuario_id
            )
        except RedisError:
            raise HTTPException(
                status_code=503,
                detail="No se pudo liberar la reserva."
            )

        if isinstance(error, HTTPException):
            raise error

        raise HTTPException(
            status_code=503,
            detail="No se pudo completar la reserva."
        )

    return {
        "mensaje": "Asientos reservados correctamente.",
        "funcion_id": funcion_id,
        "asientos": solicitados,
        "duracion_segundos": TIEMPO_RESERVA
    }

    if isinstance(error, HTTPException):
        raise error

    raise HTTPException(
        status_code=503,
        detail="No se pudo completar la reserva."
    )

    if isinstance(error, HTTPException):
        raise error

    raise HTTPException(
        status_code=503,
        detail="No se pudo completar la reserva."
    )
    return {
        "mensaje": "Asientos reservados correctamente.",
        "funcion_id": funcion_id,
        "asientos": solicitados,
        "duracion_segundos": TIEMPO_RESERVA
    }



# 6. CONSULTAR ASIENTOS DE UNA SALA


@router.get("/sala/{sala_id}")
def obtener_asientos_sala(sala_id: str):
    sala_oid = convertir_id(sala_id)

    sala = db["salas"].find_one({
        "_id": sala_oid
    })

    if not sala:
        raise HTTPException(
            status_code=404,
            detail="Sala no encontrada."
        )

    filas, por_fila = obtener_distribucion(sala)

    asientos = [
        {
            "codigo": generar_codigo(fila, numero),
            "fila": fila,
            "numero": numero
        }
        for fila in range(1, filas + 1)
        for numero in range(1, por_fila + 1)
    ]

    return {
        "sala": serializar_documento(sala),
        "total": len(asientos),
        "asientos": asientos
    }
