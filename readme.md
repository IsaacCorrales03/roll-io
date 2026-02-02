# Proyecto D&D Web — Estado, evaluación y hoja de ruta

## 1. Visión resumida

El proyecto apunta correctamente a construir un **motor D&D 5e centrado en reglas**, no un VTT genérico. Las decisiones clave (modelos de dominio, features como código, eventos, TurnManager) están bien orientadas y son coherentes con el objetivo de competir directamente con Roll20 en D&D.

No obstante, el sistema está **a medio camino** entre un modelo de datos enriquecido y un **motor de simulación completo**. El siguiente salto es estructural, no cosmético.

---

## 2. Qué está realizado (estado actual real)

### 2.1 Arquitectura general

* Backend en **Flask** con separación clara:

  * `models/`: dominio D&D
  * `services/`: persistencia y lógica de aplicación
  * `routes/`: API REST
* Dominio modelado explícitamente (buena señal):

  * `Actor`, `Character`, `Enemy`
  * `Race`, `DnDClass`, `ClassFeature`
  * `Weapon`

### 2.2 Núcleo de reglas (parcial pero prometedor)

* **Actor** como entidad central (correcto).
* Sistema de **acciones abstractas** (`Action`) con:

  * `requirements()`
  * `resolve()`
* Primer intento serio de **sistema de eventos** (`Event`, `EventListener`).
* `TurnManager` con:

  * Iniciativa
  * Orden de turnos
  * Rondas

Esto confirma que el proyecto **no está orientado a macros**, sino a reglas codificadas.

### 2.3 Features de clase

* `ClassFeature` existe como concepto.
* Ejemplo real: `UnarmoredDefense`.
* Features pueden:

  * Aplicarse al actor
  * Modificar AC mediante fórmulas

### 2.4 Persistencia

* Repositorios y mappers para `Character`.
* Base de datos integrada.

### 2.5 Frontend / API

* Endpoints funcionales para:

  * Razas
  * Clases
  * Personajes
* Inicio de integración frontend-backend.

---

## 3. Evaluación crítica del estado

### 3.1 Condición general

**Estado:** funcional pero incompleto.

El proyecto:

* ✔ Tiene buen diseño conceptual
* ✔ Tiene código de dominio real
* ✘ No tiene todavía un motor determinista cerrado
* ✘ Mezcla responsabilidades (algunas reglas aún son pasivas)

No está roto. **Está inmaduro**.

### 3.2 Problemas estructurales detectados

#### A. Sistema de eventos incompleto

* Existe, pero:

  * No es el eje del sistema
  * No todas las acciones emiten eventos
  * Las features no reaccionan de forma consistente

#### B. Personaje aún pasivo

* `Character` contiene datos y algunas reglas
* Pero no:

  * Valida acciones de forma global
  * Decide qué puede o no hacer en cada estado

#### C. Combate no es transaccional

* El ataque no es una operación atómica
* Falta:

  * Pipeline claro de resolución
  * Hooks de pre / post daño

#### D. TurnManager aislado

* Gestiona turnos, pero no gobierna el combate como sistema

---

## 4. Qué debemos realizar (sin expandir alcance)

### Objetivo inmediato

Convertir lo existente en un **motor D&D ejecutable**, no añadir features nuevas.

No UI nueva. No mapas. No marketplace.

---

## 5. Siguiente etapa: definición estricta

### Nombre de la etapa

**Cierre del núcleo de reglas (Core Lock-in)**

### Propósito

Garantizar que:

* Toda acción pasa por el motor
* Toda regla es código
* Todo efecto es reproducible

---

## 6. Lista de pasos necesarios (orden no negociable)

### Paso 1 — Formalizar el motor de eventos

* Diseñar y cerrar el **contrato del sistema de eventos** (`EVENT_SYSTEM.md`).
* Implementar `Event`, `EventBus` y tests básicos (orden, mutabilidad, cancelación).
* Ninguna feature se implementa antes de que este sistema esté estable y testeado.

---

### Paso 2 — Diseñar el sistema de acciones

* Diseñar y documentar el **contrato del sistema de acciones** (`ACTION_SYSTEM.md`).
* Separar explícitamente:

  * `Command` (intención del jugador)
  * `Action` (resolución del motor)
  * `Event` (hechos del sistema)
* Definir costes, validación, ejecución transaccional y relación con eventos.
* Implementar una acción canónica (`AttackAction`) con tests.

---

### Paso 2 — Convertir features en sistemas reactivos

* Cada `ClassFeature` debe:

  * Escuchar eventos
  * Modificar comportamiento dinámicamente

Ejemplo:

* Rage escucha `OnDamageTaken`
* Unarmored Defense escucha `OnArmorCheck`

---

### Paso 3 — Acciones como transacciones

* Un ataque debe:

  1. Validarse
  2. Ejecutarse
  3. Emitir eventos
  4. Aplicar efectos
  5. Confirmarse

Si algo falla, no se aplica nada.

---

### Paso 4 — CombatManager real

* Encapsular:

  * TurnManager
  * Estado del combate
  * Participantes
* El combate no depende del frontend.

---

### Paso 5 — Personaje como agente

* El `Actor` debe poder responder:

  * “¿Qué puedo hacer ahora?”
  * “¿Esta acción es legal?”

Eliminar decisiones en UI.

---

### Paso 6 — Tests de reglas

* Tests obligatorios para:

  * Iniciativa
  * Ataque básico
  * Feature activa
  * Evento encadenado

Sin tests → no avanzar.

---

## 7. Veredicto final

### Evaluación honesta

* **Diseño:** sólido
* **Dirección:** correcta
* **Estado:** intermedio
* **Riesgo actual:** dispersión prematura

### Siguiente paso concreto recomendado

No añadir nada nuevo.

👉 **Elegir UNA feature de clase (Rage o Sneak Attack)** y:

* Implementarla 100% vía eventos
* Usarla como patrón obligatorio

Ese paso transforma el proyecto de “prometedor” a “irreversible”.

A partir de ahí, el camino ya no se parece a Roll20.
Se parece a un motor D&D real.
