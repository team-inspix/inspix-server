# coding: utf-8
from __future__ import unicode_literals

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import hashlib
from datetime import datetime
import sqlite3


# global variables
app = Flask('inspix')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['JSON_AS_ASCII'] = False 
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
    
def make_error_json(errorstr):
    json = {
        "data": {},
        "error": [errorstr]
    }
    return jsonify(json)

def make_data_json(data):
    json = {
        "data": data,
        "error": []
    }
    return jsonify(json)
    
@app.route('/register', methods=['POST'])
def register():
    response = dict()
    try:
        jsondata = request.json
        user = User(jsondata['name'],  jsondata['password'])
        db.session.add(user)
        db.session.commit()
        
        response = {"id": user.id}
        
    except Exception as e:
        return make_error_json("ユーザ名は既に使用されています")
        #return make_error_json(str(type(e)))
        
    return make_data_json(response)

if __name__ == '__main__':
    app.run(port=5000, debug=True)