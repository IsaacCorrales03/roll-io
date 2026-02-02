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
