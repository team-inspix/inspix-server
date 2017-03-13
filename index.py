from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import hashlib
from datetime import datetime

# global variables
app = Flask('inspix')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)

# constants
default_image_url = 'https://theoldmoon0602.tk/bin/theoldmoon0602.png'
password_salt = 'INSPIX_VULNERABLE_SALT'

# Models
class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True)
    password = db.Column(db.String)
    created_at = db.Column(db.DateTime)
    face_image = db.Column(db.String)
    
    def __init__(self, username, password, face_image=default_image_url, id=None):
        if id:
            self.id = id
        self.username = username
        self.face_image = face_image
        self.password = self.generate_password(password)
        self.created_at = datetime.utcnow()
    
    def generate_password(self, password):
        return hashlib.sha256(password_salt+password).hexdigest()
        
    def check_password(self, password):
        return self.password == self.generate_password(password)

if __name__ == '__main__':
    app.run(port=5000, debug=True)