import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv(
    "MONGO_URI",
    "mongodb://localhost:27017/"
)

DB_NAME = os.getenv(
    "DB_NAME",
    "cine_db"
)

client = MongoClient(
    MONGO_URI,
    serverSelectionTimeoutMS=5000
)

db = client[DB_NAME]


def verificar_conexion():
    try:
        client.admin.command("ping")
        return True
    except Exception as error:
        print(f"Error de conexión con MongoDB: {error}")
        return False


def serializar_documento(documento):
    """
    Convierte los ObjectId y documentos BSON
    a estructuras compatibles con JSON.
    """
    from bson import ObjectId

    if isinstance(documento, ObjectId):
        return str(documento)

    if isinstance(documento, dict):
        return {
            clave: serializar_documento(valor)
            for clave, valor in documento.items()
        }

    if isinstance(documento, list):
        return [
            serializar_documento(elemento)
            for elemento in documento
        ]

    return documento