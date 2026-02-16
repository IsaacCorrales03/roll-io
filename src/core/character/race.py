# Atributos válidos del sistema (estilo D&D)
ATTRIBUTE_KEYS = set((
    "STR",
    "DEX",
    "CON",
    "INT",
    "WIS",
    "CHA"
))

# Valores base antes de aplicar bonificadores raciales
BASE_ATTRIBUTES = {
    "STR": 10,
    "DEX": 10,
    "CON": 10,
    "INT": 10,
    "WIS": 10,
    "CHA": 10
}


class Race:
    def __init__(
        self,
        name: str,
        key: str,
        description: str,
        racial_bonus_stats: dict,
        special_traits: dict
    ):
        # Nombre visible de la raza
        self.name = name

        # Identificador interno (clave lógica)
        self.key = key

        # Descripción narrativa
        self.description = description

        # Atributos base inicializados desde el estándar
        self.attributes = BASE_ATTRIBUTES.copy()

        # Bonificadores raciales a los atributos
        self.racial_bonus_stats = racial_bonus_stats

        # Aplicación de los bonificadores raciales
        for key, bonus in racial_bonus_stats.items():
            if key in self.attributes:
                self.attributes[key] += bonus

        # Rasgos especiales propios de la raza
        self.special_traits = special_traits or {}

human = Race(
    name="Humano",
    key="Human",
    description="Raza versátil y adaptable, sin especialización extrema. +1 a todos los atributos base, capaz de desempeñar cualquier rol.",
    racial_bonus_stats={"STR":1,"DEX":1,"CON":1,"INT":1,"WIS":1,"CHA":1},
    special_traits={"Versatilidad": "Capaz de desempeñar cualquier rol con eficacia."}
)

high_elf = Race(
    name="Elfo",
    key="Elf",
    description="Los elfos circulan libremente por las tierras de los humanos, donde siempre son bienvenidos pero nunca se encuentran como en casa. Son gentes conocidas por su poesía, baile, canto, saber y artes mágicas, y gustan de las cosas cuya belleza sea natural y sencilla.",
    racial_bonus_stats={"DEX": 2, "INT": 1},
    special_traits={"Darkvision": "Puede ver en la oscuridad hasta 60 pies."}
)

mountain_dwarf = Race(
    name="Enano",
    key="Dwarf",
    description="Los enanos son conocidos por su habilidad en el arte de la guerra, su gran resistencia a los castigos, su conocimiento de los secretos de la tierra, su dedicación al trabajo y su capacidad para beber cerveza. Los enanos son gente poco dada a las risas o las bromas, y suelen mostrarse recelosos con los desconocidos; sin embargo, se comportan de forma generosa con los que se ganan su confianza.",
    racial_bonus_stats={"STR": 2,"CON": 2},
    special_traits={"Resistencia": "Ventaja contra veneno y resistencia al daño por veneno."}
)

dragonborn = Race(
    name="Dracónido",
    key="DragonBorn",
    description="Tu herencia dracónida se manifiesta en una serie de rasgos que compartes con otros dracónidos. Los dracónidos tienden hacia los extremos en la guerra cósmica entre el bien y el mal. La mayoría son buenos, pero los que se ponen de lado del mal pueden ser terriblemente malignos.",
    racial_bonus_stats={"STR": 2,"CHA": 1},
    special_traits={"Aliento dracónico": "Ataque de área con daño elemental según el linaje."}
)

deep_gnome = Race(
    name="Gnomo",
    key="Gnome",
    description="Gnomo subterráneo, astuto y perceptivo. Inteligente y ágil, especializado en magia y habilidades de exploración bajo tierra.",
    racial_bonus_stats={"INT": 2,"DEX": 1},
    special_traits={"Resistencia mágica": "Ventaja en tiradas de salvación contra magia."}
)


tiefling = Race(
    name="Tiefling",
    key="Tiefling",
    description="Puede que los tieflings no tengan una tendencia innata hacia el mal, pero muchos de ellos acaban ahí. Maligna o no, una fuerza externa inclina a muchos tieflings hacia un alineamiento caótico.",
    racial_bonus_stats={"INT": 1,"CHA": 2},
    special_traits={"Resistencia al fuego": "Resistencia al daño por fuego."}
)
mediano = Race(
    name="Mediano",
    key="Halfling",
    description="Tu personaje mediano tiene unos cuantos rasgos en común con el resto de medianos. La mayoría de los medianos son neutrales buenos. Como norma general, tienen buen corazón y son amables, odian ver a otros sufrir y no toleran la opresión. También son pacíficos y tradicionales, tienen una fuerte tendencia a apoyar a su comunidad y nunca renuncian a la comodidad de sus costumbres.",
    racial_bonus_stats={"DEX": 3},
    special_traits={"Suerte": "Puede repetir una tirada de 1 en una tirada de ataque, prueba de habilidad o tirada de salvación."}

)
semi_elf = Race(
    name="Semielfo",
    key="SemiElf",
    description="Tu personaje semielfo tiene algunas cracterísticas en común con los elfos y otras que son únicas para los semielfos. Los semielfos comparten la inclinación caótica de su herencia élfica. Valoran tanto la libertad personal como la expresión de la creatividad y no demuestran ni amor por los líderes ni deseo de tener seguidores. Les irritan las reglas, se ofenden ante las exigencias de los demás y a veces son poco fiables o, al menos, impredecibles.",
    racial_bonus_stats={"CHA": 2, "DEX": 1},
    special_traits={"Visión en la oscuridad": "Puede ver en la oscuridad hasta 60 pies."}
)

RACE_MAP: dict[str, Race] = {
    "Human": human,
    "Elf": high_elf,
    "Dwarf": mountain_dwarf,
    "DragonBorn": dragonborn,
    "Gnome": deep_gnome,
    "Tiefling": tiefling,
    "Halfling": mediano,
    "SemiElf": semi_elf
}