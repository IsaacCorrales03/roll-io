# sections/infrastructure/mysql_section_repository.py

from uuid import UUID
from src.shared.database.db_service import DatabaseService
from ..ports.section_repository import SectionRepository

class MySQLSectionRepository(SectionRepository):

    def __init__(self, db: DatabaseService):
        self.db = db

    def create(self, section_data: dict) -> None:
        cur = self.db.cursor()
        cur.execute(
            """
            INSERT INTO sections (
                id, scene_id, name, texture_url,
                offset_x, offset_y, width_px, height_px,
                tile_size, grid_type
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                section_data["id"],
                section_data["scene_id"],
                section_data["name"],
                section_data["texture_url"],
                section_data["offset_x"],
                section_data["offset_y"],
                section_data["width_px"],
                section_data["height_px"],
                section_data["tile_size"],
                section_data["grid_type"],
            )
        )
        self.db.commit()

    def get_by_id(self, section_id: UUID | str) -> dict | None:
        if isinstance(section_id, UUID):
            section_id = str(section_id)

        cur = self.db.cursor(dictionary=True)
        cur.execute(
            "SELECT * FROM sections WHERE id = %s LIMIT 1",
            (section_id,)
        )
        return cur.fetchone()

    def get_by_scene(self, scene_id: UUID | str) -> list[dict]:
        if isinstance(scene_id, UUID):
            scene_id = str(scene_id)

        cur = self.db.cursor(dictionary=True)
        cur.execute(
            "SELECT * FROM sections WHERE scene_id = %s",
            (scene_id,)
        )
        return cur.fetchall()

    def delete(self, section_id: UUID | str) -> None:
        if isinstance(section_id, UUID):
            section_id = str(section_id)

        cur = self.db.cursor()
        cur.execute(
            "DELETE FROM sections WHERE id = %s",
            (section_id,)
        )
        self.db.commit()
