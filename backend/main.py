from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database.conexion import verificar_conexion

from routers import peliculas
from routers import cines
from routers import salas
from routers import funciones
from routers import asientos
from routers import usuarios
from routers import compras
from routers import boletos


app = FastAPI(
    title="CineNow API",
    description="Sistema de gestión y venta de boletos de cine.",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://127.0.0.1",
        "http://localhost:80",
        "http://127.0.0.1:80"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.get("/", tags=["Inicio"])
def inicio():
    return {
        "proyecto": "CineNow",
        "mensaje": "Bienvenido a CineNow API",
        "estado": "Backend funcionando"
    }


@app.get("/conexion", tags=["Base de datos"])
def comprobar_conexion():
    if verificar_conexion():
        return {
            "conexion": "exitosa",
            "base_de_datos": "cine_db"
        }

    return {
        "conexion": "fallida",
        "mensaje": "No se pudo conectar con MongoDB"
    }


app.include_router(peliculas.router)
app.include_router(cines.router)
app.include_router(salas.router)
app.include_router(funciones.router)
app.include_router(asientos.router)
app.include_router(usuarios.router)
app.include_router(compras.router)
app.include_router(boletos.router)