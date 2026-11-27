import os
import json
import pika

from dotenv import load_dotenv

load_dotenv()

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", "5672"))

COLA_BOLETOS = "generar_boleto"


def publicar_compra_pagada(compra_id):
    conexion = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=RABBITMQ_HOST,
            port=RABBITMQ_PORT,
            blocked_connection_timeout=5,
            socket_timeout=5
        )
    )

    try:
        canal = conexion.channel()

        canal.queue_declare(
            queue=COLA_BOLETOS,
            durable=True
        )

        canal.confirm_delivery()

        mensaje = {
            "evento": "compra_pagada",
            "compra_id": str(compra_id)
        }

        canal.basic_publish(
            exchange="",
            routing_key=COLA_BOLETOS,
            body=json.dumps(mensaje),
            mandatory=True,
            properties=pika.BasicProperties(
                delivery_mode=2,
                content_type="application/json"
            )
        )

        print(f"Compra enviada a RabbitMQ: {compra_id}")

    finally:
        conexion.close()