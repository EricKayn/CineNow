import time

from services.outbox_service import publicar_eventos_pendientes


def iniciar_outbox():

    print("Publicador de CineNow iniciado.")
    print("Buscando compras pendientes de publicar...")

    try:
        while True:

            try:
                publicar_eventos_pendientes()

            except Exception as error:
                print(f"Error en Outbox: {error}")

            time.sleep(3)

    except KeyboardInterrupt:
        print("Publicador detenido.")


if __name__ == "__main__":
    iniciar_outbox()