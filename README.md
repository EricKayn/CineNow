
# CineNow

Sistema web de reservación y compra de boletos de cine.

## Descripción

CineNow es una aplicación web que permite consultar la cartelera, seleccionar funciones, elegir asientos y realizar compras simuladas de boletos de cine.

El proyecto cuenta con una interfaz web y una API REST que administra películas, cines, salas, funciones, usuarios, compras y boletos.

## Tecnologías utilizadas

### Frontend
- HTML5
- CSS3
- JavaScript

### Backend
- Python
- FastAPI
- MongoDB
- Redis
- JWT para autenticación

## Funcionalidades

- Registro e inicio de sesión.
- Consulta de cartelera.
- Visualización de información de películas.
- Selección de fechas y funciones.
- Selección y reserva temporal de asientos.
- Simulación de compra de boletos.
- Generación de boletos.
- Consulta del historial de compras y boletos.

## Estructura del proyecto

- `frontend/`: interfaz web.
- `backend/`: API REST, modelos, rutas y servicios.
- `backend/database/`: conexión con MongoDB.
- `backend/requirements.txt`: dependencias de Python.
- `backend/.env.example`: ejemplo de configuración.

## Estado del proyecto

Proyecto académico funcional desarrollado con fines educativos para la materia de BD noSQL.

El sistema utiliza una simulación de pago y no procesa transacciones bancarias reales.
