# Roll-IO

![License](https://img.shields.io/badge/license-Unlicense-blue.svg)
![Python](https://img.shields.io/badge/python-3.12%2B-blue)
![Status](https://img.shields.io/badge/status-active--development-orange)
![Architecture](https://img.shields.io/badge/architecture-hexagonal-critical)

## ¿Qué es Roll-IO?

Roll-IO es una **Virtual Tabletop (VTT)** open source y gratuita, construida exclusivamente para **Dungeons & Dragons 5th Edition**. Su objetivo no es replicar visualmente plataformas como Roll20, sino proporcionar una **base técnica sólida** donde las reglas de D&D 5e existen como dominio puro, testeables y desacopladas de cualquier infraestructura.

En términos prácticos: múltiples jugadores pueden conectarse en tiempo real a una campaña, mover tokens sobre un mapa de cuadrícula, atacarse entre sí con resolución automática de reglas, gestionar inventarios, y un Dungeon Master puede orquestar enemigos y loot desde un panel dedicado. Todo esto sin depender de servicios de terceros ni código propietario.

## La idea central

La apuesta arquitectónica del proyecto es que **el motor de juego no sabe que existe un servidor web**. Las reglas de D&D — cálculo de AC, tiradas de ataque, estados de combate, rabia del Bárbaro, canción de descanso del Bardo — viven en `src/core` como clases Python sin ninguna dependencia HTTP, SQL ni WebSocket. Esto hace que sea trivial testear el dominio aislado, y que reemplazar MySQL por otro motor de persistencia no requiera tocar ninguna regla de juego.

La comunicación en tiempo real ocurre por WebSocket (Flask-SocketIO). El backend HTTP sirve las páginas Jinja2 y expone una API REST para operaciones sin estado (crear personaje, cargar campañas). El frontend JavaScript establece la conexión Socket.IO al entrar al juego y escucha eventos del servidor para sincronizar el estado visual.

## Flujo general de una sesión

```
1. El DM crea una campaña → se genera un mundo con un mapa
2. El DM inicia la partida → se genera un código de lobby
3. Los jugadores se unen con el código → seleccionan su personaje
4. El DM inicia la campaña → todos son redirigidos a /game
5. En /game: cada cliente conecta por WebSocket, carga recursos (tokens, mapa, personajes)
6. El DM puede mover tokens, crear enemigos, dar ítems
7. Los jugadores pueden atacar, ver su hoja de personaje, chatear
8. Al terminar: "save_and_exit" serializa todos los personajes a MySQL y limpia el estado en memoria
```

## Estructura del proyecto

```
roll-io/
├── app.py                          # Punto de entrada: inicializa Flask + SocketIO
├── requirements.txt
├── public/
│   ├── templates/                  # HTML Jinja2 (index, login, register, dashboard,
│   │                               #   create_char, create_campaign, lobby, game)
│   └── static/
│       ├── css/                    # Estilos por página
│       └── js/                     # Lógica de cliente (game.js, lobby.js, create_char.js, ...)
├── src/
│   ├── core/                       # Motor de juego puro (sin dependencias externas)
│   │   ├── base.py                 # Clases abstractas: Actor, Action, BaseEntity
│   │   ├── character/              # Character, DnDClass, Race, ClassFeature, ProgressionSystem, Enemy
│   │   ├── game/                   # GameState, Event, EventDispatcher, EventHandlers, Actions, Commands, Queries
│   │   └── items/                  # Item, Weapon, Armor, Shield, ItemInstance, catálogo ITEMS
│   ├── features/                   # Módulos de aplicación (Hexagonal)
│   │   ├── auth/                   # domain / ports / infrastructure / application
│   │   ├── campaigns/              # domain / ports / infrastructure / application
│   │   ├── characters/             # application / infrastructure
│   │   └── world/                  # domain / ports / infrastructure / application
│   ├── interfaces/
│   │   ├── http/                   # Flask app factory + blueprints de rutas
│   │   └── websocket/              # Todos los handlers de Socket.IO
│   └── shared/
│       ├── database/               # db_config, db_service (MySQL)
│       ├── utils/                  # auth_utils, campaign_utils, game_state_builder, items_utils, tokens_utils
│       └── validators/             # form_validators, service_validator
└── storage/
    └── uploads/                    # Imágenes subidas (mapas, enemigos)
```

## Stack tecnológico

| Capa | Tecnología |
|---|---|
| Backend | Python 3.12+, Flask |
| Tiempo real | Flask-SocketIO + eventlet |
| Persistencia | MySQL (vía conector propio) |
| Auth | Sesiones en DB + bcrypt |
| Frontend | HTML/CSS/JS vanilla + Jinja2 |
| Arquitectura | Hexagonal (Ports & Adapters) |

## Instalación

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Configurar las variables de entorno o el archivo de configuración de base de datos antes de iniciar.

```bash
python app.py
```

El servidor arranca en `http://0.0.0.0:5000`.

## Licencia

**The Unlicense** — dominio público. Uso, modificación y distribución libres sin restricción.