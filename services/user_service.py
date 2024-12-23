from models import db, User, Role
from flask_security.utils import hash_password
from typing import List


class UserService:
    @staticmethod
    def create_user(first_name: str, last_name: str,
                    email: str,
                    password: str,
                    roles: List[Role] = None) -> User:
        user = User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=hash_password(password),
            roles=roles or []
        )
        db.session.add(user)
        db.session.commit()
        return user

    @staticmethod
    def get_user_by_email(email: str) -> User:
        return User.query.filter_by(email=email).first()

    @staticmethod
    def list_users() -> List[User]:
        return User.query.all()

    @staticmethod
    def delete_user(user: User):
        db.session.delete(user)
        db.session.commit()
