
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from itertools import cycle
from bson import ObjectId

from database.conexion import db



# CONFIGURACIÓN


DIAS = 30
ZONA = ZoneInfo("America/Mexico_City")

HORARIOS = [12, 16, 20]

PRECIOS = {
    "2D": 85.0,
    "3D": 110.0,
    "IMAX": 145.0
}



# PELÍCULAS


PELICULAS = [
    {
        "titulo": "Interestelar",
        "genero": "Ciencia ficción",
        "duracion": 169,
        "clasificacion": "B",
        "sinopsis": "Un grupo de astronautas viaja más allá de nuestra galaxia para buscar un nuevo hogar para la humanidad.",
        "poster": "https://image.tmdb.org/t/p/w500/gEU2QniE6E77NI6lCU6MxlNBvIx.jpg"
    },
    {
        "titulo": "El origen",
        "genero": "Ciencia ficción",
        "duracion": 148,
        "clasificacion": "B",
        "sinopsis": "Un especialista en infiltrarse en los sueños recibe una misión imposible.",
        "poster": "https://image.tmdb.org/t/p/w500/oYuLEt3zVCKq57qu2F8dT7NIa6f.jpg"
    },
    {
        "titulo": "Avatar: El camino del agua",
        "genero": "Aventura",
        "duracion": 192,
        "clasificacion": "B",
        "sinopsis": "Jake Sully y su familia enfrentan nuevas amenazas en Pandora.",
        "poster": ""
    },
    {
        "titulo": "Spider-Man: Sin camino a casa",
        "genero": "Acción",
        "duracion": 148,
        "clasificacion": "B",
        "sinopsis": "Peter Parker enfrenta consecuencias inesperadas al intentar recuperar su identidad secreta.",
        "poster": ""
    },
    {
        "titulo": "Coco",
        "genero": "Animación",
        "duracion": 105,
        "clasificacion": "A",
        "sinopsis": "Miguel viaja al mundo de los muertos para descubrir la historia de su familia.",
        "poster": ""
    },
    {
        "titulo": "Intensamente 2",
        "genero": "Animación",
        "duracion": 96,
        "clasificacion": "A",
        "sinopsis": "Nuevas emociones llegan a la mente de Riley durante su adolescencia.",
        "poster": ""
    },
    {
        "titulo": "Duna: Parte Dos",
        "genero": "Ciencia ficción",
        "duracion": 166,
        "clasificacion": "B",
        "sinopsis": "Paul Atreides se une a los fremen mientras enfrenta su destino en Arrakis.",
        "poster": ""
    },
    {
        "titulo": "Oppenheimer",
        "genero": "Drama",
        "duracion": 180,
        "clasificacion": "B15",
        "sinopsis": "La historia del físico que dirigió el desarrollo de la primera bomba atómica.",
        "poster": ""
    },
    {
        "titulo": "El conjuro",
        "genero": "Terror",
        "duracion": 112,
        "clasificacion": "B15",
        "sinopsis": "Dos investigadores paranormales ayudan a una familia aterrorizada por una presencia sobrenatural.",
        "poster": ""
    },
    {
        "titulo": "Jurassic World",
        "genero": "Aventura",
        "duracion": 124,
        "clasificacion": "B",
        "sinopsis": "Un parque temático de dinosaurios enfrenta el escape de una criatura peligrosa.",
        "poster": ""
    },
    {
        "titulo": "Batman: El caballero de la noche",
        "genero": "Acción",
        "duracion": 152,
        "clasificacion": "B",
        "sinopsis": "Batman enfrenta al Joker mientras intenta proteger Ciudad Gótica.",
        "poster": ""
    },
    {
        "titulo": "Super Mario Bros.: La película",
        "genero": "Animación",
        "duracion": 92,
        "clasificacion": "A",
        "sinopsis": "Mario viaja al Reino Champiñón para rescatar a su hermano Luigi.",
        "poster": ""
    }
]



# CINES


CINES = [
    {
        "nombre": "Cine Centro",
        "direccion": "Centro, Ciudad de México",
        "ciudad": "Ciudad de México",
        "estado": "activo"
    },
    {
        "nombre": "Cine Plaza",
        "direccion": "Zona Norte, Ciudad de México",
        "ciudad": "Ciudad de México",
        "estado": "activo"
    },
    {
        "nombre": "Cine Universidad",
        "direccion": "Coyoacán, Ciudad de México",
        "ciudad": "Ciudad de México",
        "estado": "activo"
    },
    {
        "nombre": "Cine Reforma",
        "direccion": "Paseo de la Reforma, Ciudad de México",
        "ciudad": "Ciudad de México",
        "estado": "activo"
    }
]



# CREAR O REUTILIZAR PELÍCULAS


def cargar_peliculas():
    resultado = []

    for datos in PELICULAS:
        pelicula = db["peliculas"].find_one({
            "titulo": datos["titulo"]
        })

        if pelicula is None:
            identificador = db["peliculas"].insert_one(
                datos.copy()
            ).inserted_id
            pelicula = db["peliculas"].find_one({
                "_id": identificador
            })

        resultado.append(pelicula)

    return resultado



# CREAR O REUTILIZAR CINES


def cargar_cines():
    resultado = []

    for datos in CINES:
        cine = db["cines"].find_one({
            "nombre": datos["nombre"]
        })

        if cine is None:
            identificador = db["cines"].insert_one(
                datos.copy()
            ).inserted_id
            cine = db["cines"].find_one({
                "_id": identificador
            })

        resultado.append(cine)

    return resultado



# CREAR O REUTILIZAR SALAS


def cargar_salas(cines):
    resultado = []

    configuraciones = [
        ("Sala 1", 8, 10),
        ("Sala 2", 10, 12),
        ("Sala 3", 6, 8)
    ]

    for cine in cines:
        for nombre, filas, columnas in configuraciones:
            sala = db["salas"].find_one({
                "cine_id": cine["_id"],
                "nombre": nombre
            })

            if sala is None:
                datos = {
                    "cine_id": cine["_id"],
                    "nombre": nombre,
                    "filas": filas,
                    "asientos_por_fila": columnas,
                    "capacidad": filas * columnas,
                    "estado": "activa"
                }

                identificador = db["salas"].insert_one(
                    datos
                ).inserted_id

                sala = db["salas"].find_one({
                    "_id": identificador
                })

            if (
                sala.get("estado") == "activa"
                and sala.get("filas", 0) > 0
                and sala.get("asientos_por_fila", 0) > 0
            ):
                resultado.append({
                    "cine": cine,
                    "sala": sala
                })

    return resultado



# CREAR FUNCIONES FUTURAS


def cargar_funciones(peliculas, salas):
    creadas = 0
    existentes = 0

    inicio = (
        datetime.now(ZONA).date()
        + timedelta(days=1)
    )

    turno_peliculas = cycle(peliculas)

    for dia in range(DIAS):
        fecha = inicio + timedelta(days=dia)

        for relacion in salas:
            cine = relacion["cine"]
            sala = relacion["sala"]

            for indice, hora in enumerate(HORARIOS):
                pelicula = next(turno_peliculas)

                fecha_local = datetime(
                    fecha.year,
                    fecha.month,
                    fecha.day,
                    hora,
                    0,
                    tzinfo=ZONA
                )

                fecha_utc = fecha_local.astimezone(
                    timezone.utc
                )

                formato = (
                    "2D" if indice == 0
                    else "3D" if indice == 1
                    else "IMAX"
                )

                idioma = (
                    "Español" if indice % 2 == 0
                    else "Subtitulada"
                )

                conflicto = db["funciones"].find_one({
                    "sala_id": sala["_id"],
                    "fecha_hora": fecha_utc,
                    "estado": "programada"
                })

                if conflicto:
                    existentes += 1
                    continue

                db["funciones"].insert_one({
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
                })

                creadas += 1

    return creadas, existentes



# EJECUCIÓN


def main():
    print("Cargando cartelera de CineNow...")

    peliculas = cargar_peliculas()
    cines = cargar_cines()
    salas = cargar_salas(cines)

    creadas, existentes = cargar_funciones(
        peliculas,
        salas
    )

    print()
    print("Carga finalizada.")
    print(f"Películas disponibles: {len(peliculas)}")
    print(f"Cines disponibles: {len(cines)}")
    print(f"Salas disponibles: {len(salas)}")
    print(f"Funciones creadas: {creadas}")
    print(f"Funciones ya existentes: {existentes}")


if __name__ == "__main__":
    main()
