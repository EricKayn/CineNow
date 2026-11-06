
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from itertools import cycle
from bson import ObjectId

from database.conexion import db



# CONFIGURACIÓN


DIAS_A_GENERAR = 30
MAX_FUNCIONES_POR_DIA = 3

HORARIOS = [12, 16, 20]

FORMATOS = ["2D", "3D", "IMAX"]
IDIOMAS = ["Español", "Subtitulada"]

PRECIOS = {
    "2D": 85.0,
    "3D": 110.0,
    "IMAX": 145.0
}

ZONA_HORARIA = ZoneInfo("America/Mexico_City")



# CONVERTIR IDENTIFICADORES


def convertir_objectid(valor):
    if isinstance(valor, ObjectId):
        return valor

    if isinstance(valor, dict):
        valor = valor.get("$oid")

    try:
        return ObjectId(str(valor))
    except (TypeError, ValueError):
        return None



# CARGAR DATOS EXISTENTES


peliculas = list(db["peliculas"].find())
cines = list(db["cines"].find({
    "estado": "activo"
}))
salas = list(db["salas"].find({
    "estado": "activa"
}))

if not peliculas:
    raise SystemExit(
        "No hay películas registradas en MongoDB."
    )

if not cines:
    raise SystemExit(
        "No hay cines activos registrados."
    )

if not salas:
    raise SystemExit(
        "No hay salas activas registradas."
    )



# RELACIONAR SALAS CON CINES


cines_por_id = {
    str(cine["_id"]): cine
    for cine in cines
}

salas_validas = []

for sala in salas:
    cine_id = convertir_objectid(
        sala.get("cine_id")
    )

    if cine_id is None:
        continue

    cine = cines_por_id.get(str(cine_id))

    if cine is None:
        continue

    salas_validas.append({
        "sala": sala,
        "cine": cine
    })

if not salas_validas:
    raise SystemExit(
        "No se encontraron salas activas "
        "asociadas a cines activos."
    )



# GENERAR FUNCIONES FUTURAS


ahora = datetime.now(ZONA_HORARIA)
inicio = ahora.date() + timedelta(days=1)

contador_creadas = 0
contador_existentes = 0

peliculas_ciclo = cycle(peliculas)

for dia in range(DIAS_A_GENERAR):
    fecha = inicio + timedelta(days=dia)

    for relacion in salas_validas:
        sala = relacion["sala"]
        cine = relacion["cine"]

        for indice, hora in enumerate(
            HORARIOS[:MAX_FUNCIONES_POR_DIA]
        ):
            pelicula = next(peliculas_ciclo)

            fecha_local = datetime(
                fecha.year,
                fecha.month,
                fecha.day,
                hora,
                0,
                tzinfo=ZONA_HORARIA
            )

            # Guardamos en UTC para que la fecha
            # represente un instante inequívoco.
            fecha_utc = fecha_local.astimezone(
                timezone.utc
            )

            formato = FORMATOS[
                (dia + indice) % len(FORMATOS)
            ]

            idioma = IDIOMAS[
                (dia + indice) % len(IDIOMAS)
            ]

            # Evitar duplicados en la misma sala
            # y a la misma hora.
            existente = db["funciones"].find_one({
                "sala_id": sala["_id"],
                "fecha_hora": fecha_utc,
                "estado": "programada"
            })

            if existente:
                contador_existentes += 1
                continue

            funcion = {
                "pelicula_id": pelicula["_id"],
                "cine_id": cine["_id"],
                "sala_id": sala["_id"],
                "fecha_hora": fecha_utc,
                "formato": formato,
                "idioma": idioma,
                "precio": PRECIOS[formato],
                "estado": "programada",
                "creada_en": datetime.now(
                    timezone.utc
                )
            }

            db["funciones"].insert_one(funcion)

            contador_creadas += 1

            print(
                f"Creada: {fecha_local:%Y-%m-%d %H:%M} | "
                f"Cine: {cine.get('nombre', 'Sin nombre')} | "
                f"Sala: {sala.get('nombre', 'Sin nombre')} | "
                f"Película: {pelicula.get('titulo', pelicula.get('nombre', 'Sin título'))}"
            )



# RESULTADOS


print()
print("===================================")
print("CARGA DE FUNCIONES FINALIZADA")
print("===================================")
print(f"Funciones creadas: {contador_creadas}")
print(f"Funciones existentes: {contador_existentes}")
print(f"Salas utilizadas: {len(salas_validas)}")
print(f"Días programados: {DIAS_A_GENERAR}")
