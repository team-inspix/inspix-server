# coding: utf-8
from __future__ import unicode_literals

from flask import Flask, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
import hashlib
from datetime import datetime
import sqlite3
from os.path import abspath, dirname, join


# global variables
app = Flask('inspix')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + join(dirname(abspath(__file__)), 'database.db')
app.config['JSON_AS_ASCII'] = False 
app.secret_key = 'INSPIX_VULNERABLE_SECRET'

db = SQLAlchemy(app)

# constants
default_image_url = 'https://theoldmoon0602.tk/bin/theoldmoon0602.png'
password_salt = 'INSPIX_VULNERABLE_SALT'

# Models
class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String)
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


@app.route('/login', methods=['POST'])
def login():
    try:
        jsondata = request.json
        user = User.query.filter_by(id=jsondata['id']).first()
        
        if not user.check_password(jsondata['password']):
            return make_error_json("ログインに失敗しました"), 403
        
        session['user_id'] = user.id
        return make_data_json({"result": True}), 200
        
    except Exception as e:
        pass
    return make_error_json("ログインに失敗しました"), 403            

@app.route('/register', methods=['POST'])
def register():
    try:
        jsondata = request.json
        user = User(jsondata['name'],  jsondata['password'])
        db.session.add(user)
        db.session.commit()
        
        response = {"id": user.id}
        return make_data_json(response), 201
        
    except Exception as e:
        return make_error_json(e.message), 403
        
        
    return make_error_json("予期しないエラーです"), 500

            

if __name__ == '__main__':
    app.run(port=5001)
