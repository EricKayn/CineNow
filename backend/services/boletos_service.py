from datetime import datetime, timezone
from bson import ObjectId
from pymongo.errors import DuplicateKeyError

from database.conexion import db


def generar_boletos_compra(compra_id):

    compra_oid = ObjectId(compra_id)

    compra = db["compras"].find_one({
        "_id": compra_oid,
        "estado": "pagada"
    })

    if not compra:
        raise ValueError("Compra pagada no encontrada.")

    for asiento in compra["asientos"]:

        boleto = {
            "compra_id": compra_oid,
            "usuario_id": compra["usuario_id"],
            "funcion_id": compra["funcion_id"],
            "asiento": asiento,
            "codigo": f"CN-{ObjectId()}",
            "estado": "vigente",
            "creado_en": datetime.now(timezone.utc)
        }

        try:
            db["boletos"].update_one(
                {
                    "compra_id": compra_oid,
                    "asiento": asiento
                },
                {
                    "$setOnInsert": boleto
                },
                upsert=True
            )

        except DuplicateKeyError:
            if not db["boletos"].find_one({
                "compra_id": compra_oid,
                "asiento": asiento
            }):
                raise

    boletos = list(db["boletos"].find({
        "compra_id": compra_oid
    }))

    print(f"Boletos disponibles: {len(boletos)}")

    return boletos