from models.database import db
from werkzeug.security import generate_password_hash, check_password_hash


class UserService:
    @staticmethod
    def create_user(full_name, mobile, password):
        hashed_password = generate_password_hash(password, method="pbkdf2:sha256")
        db.create_user(full_name, mobile, hashed_password)

    @staticmethod
    def authenticate_user(mobile, password):
        user = db.get_user_by_mobile(mobile)
        if user and check_password_hash(user["password"], password):
            return user
        return None

    @staticmethod
    def get_user_by_id(user_id):
        user = db.get_user_by_id(user_id)
        if user:
            # Return without password (matches original SQL projection)
            return {
                'id': user['id'],
                'full_name': user['full_name'],
                'mobile': user['mobile'],
                'balance': user['balance'],
                'role': user['role'],
            }
        return None

    @staticmethod
    def update_profile(user_id, full_name):
        db.update_user_name(user_id, full_name)

    @staticmethod
    def change_password(user_id, current_password, new_password):
        user = db.get_user_by_id(user_id)
        if not user or not check_password_hash(user["password"], current_password):
            return False
        hashed_password = generate_password_hash(new_password, method="pbkdf2:sha256")
        db.update_user_password(user_id, hashed_password)
        return True

    @staticmethod
    def get_all_users():
        users = db.get_all_users()
        return [
            {
                'id': u['id'],
                'full_name': u['full_name'],
                'mobile': u['mobile'],
                'balance': u['balance'],
                'role': u['role'],
            }
            for u in users
        ]

    @staticmethod
    def get_admin_user():
        admin = db.get_admin_user()
        if admin:
            return {'id': admin['id'], 'balance': admin['balance']}
        return None

    @staticmethod
    def get_total_users():
        return db.get_total_users()

    @staticmethod
    def get_total_balance():
        return db.get_total_balance()
