from models import db, Role
from typing import List


class RoleService:
    @staticmethod
    def create_role(name: str, description: str = "") -> Role:
        role = Role(name=name, description=description)
        db.session.add(role)
        db.session.commit()
        return role

    @staticmethod
    def get_role_by_name(name: str) -> Role:
        return Role.query.filter_by(name=name).first()

    @staticmethod
    def list_roles() -> List[Role]:
        return Role.query.all()
