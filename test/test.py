from models.races import human, dragonborn
from models.dndclasses import Barbarian, Bard
from models.character import Character
from models.turnManager import TurnManager  # asumiendo que ya lo implementaste
from models.weapon import Weapon

# --- Crear personajes ---
b1 = Character(id="1", name="Thorgar", race=dragonborn, dnd_class=Barbarian())
b2 = Character(id="2", name="Lyria", race=human, dnd_class=Bard())
b3 = Character(id="3", name="Grum", race=dragonborn, dnd_class=Barbarian())

# Armas simples
sword = Weapon(name="Espada Larga", dice_count=1, dice_size=8, attribute="STR", bonus=0)
b1.equip(weapon=sword)
b3.equip(weapon=sword)

# Inicializar TurnManager (simplificado)
turn_manager = TurnManager([b1, b2, b3])

# --- Bardo da inspiración ---
b2.features[0].use(b2, turn_manager, target=b1) # type: ignore

print(b1.attack(b2))
print(f"\n{b1.name} ataca a {b3.name}:")
print(b1.attack(b2))