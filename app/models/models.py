from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, id, name, role):
        self.id = id
        self.name = name
        self.role = role

users = {'admin1': {'password': 'ss'}}

