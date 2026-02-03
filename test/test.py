from uuid import uuid4

from models.character import Character
from models.events import GameState, EventDispatcher
from models.races import human
from models.dndclasses import Bard

def main():
    # ======================
    # 1. Crear personaje Bard
    # ======================
    bard = Character(
        id=uuid4(),
        name="Himmel",
        race=human,
        dnd_class=Bard(),
    )

    # Subir al nivel 2 para desbloquear Song of Rest
    bard.levelUp()

    # Crear GameState y dispatcher
    dispatcher = EventDispatcher()
    state = GameState(
        characters={bard.id: bard},
        current_turn=1,
        current_phase="rest",
        dispatcher=dispatcher
    )

    # ======================
    # 2. Crear objetivo de curación
    # ======================
    target = Character(
        id=uuid4(),
        name="Hita",
        race=human,
        dnd_class=Bard()  # puede ser cualquier clase
    )
    target.hp -= 4  # simulamos daño
    state.characters[target.id] = target

    print("HP inicial:", target.hp, "/", target.max_hp)


    # ======================
    # 3. Usar Song of Rest
    # ======================
    song = bard.get_feature("SongOfRest")
    if song:
        event = song.use(actor=bard, state=state, targets=[target.id])

    else:
        event = None
    print("HP después:", target.hp, "/", target.max_hp)
    # ======================
    # 4. Revisar resultados
    # ======================


if __name__ == "__main__":
    main()
