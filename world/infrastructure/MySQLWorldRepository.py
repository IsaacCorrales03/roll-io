from uuid import UUID
from services.db_service import DatabaseService
from ..domain.world import World
from ..domain.scene import Scene
from ..ports.world_repository import WorldRepository


class MySQLWorldRepository(WorldRepository):

    def __init__(self, db: DatabaseService):
        self.db = db

    def save(self, world: World) -> None:
        cur = self.db.cursor()

        # World
        cur.execute(
            """
            INSERT INTO worlds (id, name, lore)
            VALUES (%s, %s, %s)
            """,
            (str(world.id), world.name, world.lore)
        )

        for scene in world.scenes:
            cur.execute(
                """
                INSERT INTO scenes (id, world_id, name, map_url, description)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    str(scene.id),
                    str(world.id),
                    scene.name,
                    scene.map_url,
                    scene.description
                )
            )

            for section in scene.sections:
                cur.execute(
                    """
                    INSERT INTO sections (
                        id, scene_id, name,
                        offset_x, offset_y,
                        width_px, height_px,
                        tile_size, grid_type,
                        texture_url
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        str(section.id),
                        str(scene.id),
                        section.name,
                        section.offset_x,
                        section.offset_y,
                        section.width_px,
                        section.height_px,
                        section.tile_size,
                        section.grid_type,
                        section.texture_url
                    )
                )

        self.db.commit()

    def get(self, world_id: UUID) -> World | None:
        cur = self.db.cursor(dictionary=True)

        cur.execute(
            "SELECT * FROM worlds WHERE id = %s LIMIT 1",
            (str(world_id),)
        )
        world_row = cur.fetchone()
        if not world_row:
            return None

        world = World(
            id=UUID(world_row["id"]),
            name=world_row["name"],
            lore=world_row["lore"],
            scenes=[]
        )

        cur.execute(
            "SELECT * FROM scenes WHERE world_id = %s",
            (str(world_id),)
        )
        scenes_rows = cur.fetchall()

        for row in scenes_rows:
            scene = Scene(
                id=UUID(row["id"]),
                world_id=UUID(row["world_id"]),
                name=row["name"],
                map_url=row["map_url"],
                description=row["description"]
            )

            cur.execute(
                "SELECT * FROM sections WHERE scene_id = %s",
                (str(scene.id),)
            )
            section_rows = cur.fetchall()

            for s in section_rows:
                from ..domain.section import Section

                section = Section(
                    id=UUID(s["id"]),
                    scene_id=UUID(s["scene_id"]),
                    name=s["name"],
                    offset_x=s["offset_x"],
                    offset_y=s["offset_y"],
                    width_px=s["width_px"],
                    height_px=s["height_px"],
                    tile_size=s["tile_size"],
                    grid_type=s["grid_type"],
                    texture_url=s["texture_url"],
                )
                scene.add_section(section)

            world.add_scene(scene)

        return world
