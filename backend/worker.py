import json
import time
import pika
from database.conexion import db

from bson.errors import InvalidId

from services.rabbitmq_service import (
    RABBITMQ_HOST,
    RABBITMQ_PORT,
    COLA_BOLETOS
)

from services.boletos_service import generar_boletos_compra


def procesar_mensaje(canal, metodo, propiedades, cuerpo):

    try:
        mensaje = json.loads(cuerpo)

        compra_id = mensaje["compra_id"]

        print(f"Procesando compra: {compra_id}")

        generar_boletos_compra(compra_id)

        canal.basic_ack(
            delivery_tag=metodo.delivery_tag
        )

        print("Mensaje procesado correctamente.")

    except (ValueError, InvalidId, KeyError, TypeError) as error:

        print(f"Mensaje invalido: {error}")

        canal.basic_nack(
            delivery_tag=metodo.delivery_tag,
            requeue=False
        )

    except Exception as error:

        print(f"Error al procesar: {error}")

        time.sleep(5)

        canal.basic_nack(
            delivery_tag=metodo.delivery_tag,
            requeue=True
        )


def iniciar_worker():

    db["boletos"].create_index(
    [("compra_id", 1), ("asiento", 1)],
    unique=True
    )

    conexion = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=RABBITMQ_HOST,
            port=RABBITMQ_PORT
        )
    )

    canal = conexion.channel()

    canal.queue_declare(
        queue=COLA_BOLETOS,
        durable=True
    )

    canal.basic_qos(prefetch_count=1)

    canal.basic_consume(
        queue=COLA_BOLETOS,
        on_message_callback=procesar_mensaje,
        auto_ack=False
    )

    print("Worker de CineNow iniciado.")
    print("Esperando compras pagadas...")

    try:
        canal.start_consuming()

    except KeyboardInterrupt:
        canal.stop_consuming()

    finally:
        if conexion.is_open:
            conexion.close()


if __name__ == "__main__":

    try:
        while True:
            try:
                iniciar_worker()
                break

            except pika.exceptions.AMQPConnectionError as error:
                print(f"Conexion perdida: {error}")
                print("Reconectando en 5 segundos...")
                time.sleep(5)

    except KeyboardInterrupt:
        print("Worker detenido.")