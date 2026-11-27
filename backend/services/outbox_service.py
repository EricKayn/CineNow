from database.conexion import db
from services.rabbitmq_service import publicar_compra_pagada


def publicar_eventos_pendientes():

    compras = db["compras"].find({
        "estado": "pagada",
        "evento_boletos_pendiente": True
    })

    for compra in compras:

        compra_id = compra["_id"]

        try:
            publicar_compra_pagada(compra_id)

            db["compras"].update_one(
                {"_id": compra_id},
                {
                    "$set": {
                        "evento_boletos_pendiente": False
                    }
                }
            )

            print(f"Evento publicado: {compra_id}")

        except Exception as error:
            print(f"Evento pendiente: {compra_id}")
            print(f"Error: {error}")