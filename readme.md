# Roll-IO

![License](https://img.shields.io/badge/license-Unlicense-blue.svg)
![Python](https://img.shields.io/badge/python-3.12%2B-blue)
![Status](https://img.shields.io/badge/status-active--development-orange)
![Architecture](https://img.shields.io/badge/architecture-hexagonal-critical)

Roll-IO es una **Virtual Tabletop (VTT)** gratuita y open source, inspirada conceptualmente en plataformas como Roll20, diseñada **exclusivamente para Dungeons & Dragons 5th Edition (D&D 5e)**. El proyecto prioriza el rigor arquitectónico, la separación estricta de responsabilidades y la extensibilidad del dominio de reglas.

El sistema no es un clon visual de Roll20. Su objetivo es proporcionar una **plataforma técnica sólida** para ejecutar, simular y gestionar campañas de D&D 5e mediante un motor de reglas propio, desacoplado de la interfaz y de la infraestructura.

---

## Objetivos del proyecto

* Implementar una VTT centrada exclusivamente en D&D 5e.
* Modelar reglas del sistema como **dominio puro**, testeable y extensible.
* Separar completamente dominio, aplicación, infraestructura y presentación.
* Permitir evolución hacia combates avanzados, estados complejos y automatización.
* Mantener el proyecto libre de dependencias propietarias.

---

## Características

* Gestión de campañas, personajes y sesiones.
* Motor de combate y acciones basado en eventos.
* Soporte explícito para ventajas, desventajas y modificadores (D&D 5e).
* Sistema de estados (stun, rage, buffs, debuffs).
* Arquitectura Hexagonal / Clean Architecture.
* Persistencia desacoplada (implementación actual: MySQL).
* Autenticación y sesiones.
* Interfaz web basada en Flask y Jinja2.

---

## Estructura del proyecto

```text
roll-io/
├── app.py
├── main.py
├── config.py
├── requirements.txt
├── auth/
├── campaigns/
├── models/
├── routes/
├── services/
├── static/
├── templates/
├── test/
└── utils/
```

---

## Descripción detallada por módulos

## Raíz

### `app.py`

Inicializa la aplicación Flask, registra blueprints y configura middlewares básicos.

### `main.py`

Punto de entrada del sistema. Controla el ciclo de vida de la aplicación.

### `config.py`

Gestión centralizada de configuración (entorno, base de datos, secretos).

### `requirements.txt`

Dependencias del proyecto, priorizando librerías estables y ampliamente adoptadas.

---

## `auth/` — Autenticación

Implementa autenticación siguiendo estrictamente **Ports & Adapters**.

```
auth/
├── domain/
├── ports/
└── infrastructure/
```

### `auth/domain/`

* `user.py`: entidad de usuario (identidad, credenciales, invariantes).
* `auth_session.py`: modelo de sesión autenticada.

Dominio completamente independiente de Flask y SQL.

### `auth/ports/`

Contratos abstractos:

* Persistencia de usuarios.
* Persistencia de sesiones.
* Hasheo de contraseñas.
* Validación de sesiones.

### `auth/infrastructure/`

Implementaciones técnicas:

* Repositorios MySQL.
* Hasher bcrypt.

---

## `campaigns/` — Campañas

Encapsula la gestión de campañas de juego.

```
campaigns/
├── domain/
├── ports/
└── infrastructure/
```

### `campaigns/domain/`

* `campaign.py`: entidad de campaña, invariantes y reglas internas.

### `campaigns/ports/`

* `campaign_repository.py`: contrato de persistencia.

### `campaigns/infrastructure/`

* `mysql_campaign_repository.py`: implementación concreta.

---

## `models/` — Dominio de D&D 5e

Este es el **núcleo conceptual del proyecto**. Aquí reside toda la lógica de D&D 5e.

### Personajes y reglas

* Clases (`Barbarian`, etc.) con habilidades modeladas como lógica de dominio.
* Razas y modificadores.
* Sistema de atributos y tiradas.

### Acciones

* Ataques.
* Tiradas de dados.
* Comandos de acción inmutables.

### Eventos

Arquitectura basada en eventos:

* `Event`
* `EventHandler`
* `EventDispatcher`

Permite composición de reglas sin condicionales rígidos.

### Estados

* Rage
* Stun
* Buffs y debuffs

Cada estado es una entidad explícita del dominio.

### Mundo

* Entidades del mundo.
* Contexto de combate.
* Representación de relaciones entre actores.

El dominio no conoce HTTP, SQL ni sesiones.

---

## `services/` — Capa de aplicación

Orquesta casos de uso:

* Creación de personajes.
* Inicio de campañas.
* Ejecución de acciones.

No contiene lógica de reglas, solo coordinación.

---

## `routes/` — Presentación HTTP

Endpoints Flask:

* Autenticación.
* Campañas.
* Personajes.
* Datos de reglas.

Adaptadores entre HTTP y servicios.

---

## `static/` y `templates/`

Capa de interfaz web:

* HTML (Jinja2).
* CSS.
* JavaScript.

Separada completamente del dominio.

---

## Arquitectura

Arquitectura **Hexagonal (Ports & Adapters)**:

* Dominio puro y central.
* Puertos como contratos.
* Infraestructura reemplazable.
* Presentación como adaptador externo.

Esta decisión es deliberada y no negociable.

---

## Instalación

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## Ejecución

```bash
python main.py
```

---

## Licencia

Este proyecto se publica bajo **The Unlicense**.

El software es de dominio público:

* Uso libre.
* Modificación libre.
* Distribución libre.
* Uso comercial permitido.

Sin garantías de ningún tipo.
