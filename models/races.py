from .race import Race

human = Race(
    name="Humano",
    key="Human",
    description="Raza versátil y adaptable, sin especialización extrema. +1 a todos los atributos base, capaz de desempeñar cualquier rol.",
    racial_bonus_stats={"STR":1,"DEX":1,"CON":1,"INT":1,"WIS":1,"CHA":1},
    special_traits={"Versatilidad": "Capaz de desempeñar cualquier rol con eficacia."}
)

high_elf = Race(
    name="Elfo Alto",
    key="Elf",
    description="Subraza de elfo enfocada en inteligencia y magia. Ágil, perceptivo y versátil, con afinidad por hechizos y habilidades arcanas.",
    racial_bonus_stats={"DEX": 2, "INT": 1},
    special_traits={"Darkvision": "Puede ver en la oscuridad hasta 60 pies."}
)

mountain_dwarf = Race(
    name="Enano de la Montaña",
    key="Dwarf",
    description="Subraza de enano fuerte y resistente. Robusto y hábil en combate cuerpo a cuerpo, con gran capacidad para cargar y soportar daño.",
    racial_bonus_stats={"STR": 2,"CON": 2},
    special_traits={"Resistencia": "Ventaja contra veneno y resistencia al daño por veneno."}
)

dragonborn = Race(
    name="Dragonborn",
    key="DragonBorn",
    description="Raza humanoide dracónica, fuerte y carismática. Destaca en combate y tiene herencia de dragón que influye en su presencia y habilidades.",
    racial_bonus_stats={"STR": 2,"CHA": 1},
    special_traits={"Aliento dracónico": "Ataque de área con daño elemental según el linaje."}
)

deep_gnome = Race(
    name="Gnomo de las Profundidades",
    key="Gnome",
    description="Gnomo subterráneo, astuto y perceptivo. Inteligente y ágil, especializado en magia y habilidades de exploración bajo tierra.",
    racial_bonus_stats={"INT": 2,"DEX": 1},
    special_traits={"Resistencia mágica": "Ventaja en tiradas de salvación contra magia."}
)



RACE_MAP: dict[str, Race] = {
    "Human": human,
    "Elf": high_elf,
    "Dwarf": mountain_dwarf,
    "DragonBorn": dragonborn,
    "Gnome": deep_gnome
}