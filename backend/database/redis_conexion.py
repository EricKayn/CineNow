
import os

import redis


# CONFIGURACIÓN DE REDIS


REDIS_URL = os.getenv(
    "REDIS_URL",
    "redis://localhost:6379/0"
)



# CLIENTE DE REDIS
redis_cliente = redis.Redis.from_url(
    REDIS_URL,
    decode_responses=True,
    socket_connect_timeout=5,
    socket_timeout=5
)



# VERIFICAR CONEXIÓN
def verificar_redis():
    try:
        return redis_cliente.ping()
    except redis.RedisError as error:
        print(f"Error de conexión con Redis: {error}")
        return False
