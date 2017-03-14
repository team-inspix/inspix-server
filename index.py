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
    username = db.Column(db.String, nullable=False)
    password = db.Column(db.String, nullable=False)
    created_at = db.Column(db.DateTime)
    face_image = db.Column(db.String)
    
    def __init__(self, username, password, face_image=default_image_url):
        self.username = username
        self.face_image = face_image
        self.password = self.generate_password(password)
        self.created_at = datetime.utcnow()
    
    def generate_password(self, password):
        return hashlib.sha256(password_salt+password).hexdigest()
        
    def check_password(self, password):
        return self.password == self.generate_password(password)

class Inspiration(db.Model):
    __tablename__ = 'inspirations'
    id = db.Column(db.Integer, primary_key=True)
    base_image_url = db.Column(db.String)
    background_image_url = db.Column(db.String)
    composited_image_url = db.Column(db.String)
    weather = db.Column(db.String)
    temperature = db.Column(db.Float)
    longitude = db.Column(db.Float)
    latitude = db.Column(db.Float)
    caption = db.Column(db.String)
    captured_time = db.Column(db.DateTime)
    
    comment = db.Column(db.String)
    is_nokkari = db.Column(db.Boolean)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    nokkari_from = db.Column(db.Integer, db.ForeignKey("inspirations.id"))
    created_at = db.Column(db.DateTime)
    
    def __init__(self, base_image_url, background_image_url, composited_image_url, caption, captured_time, author_id,
                 weather=None, temperature=None, longitude=None, latitude=None,
                 comment="", is_nokkari=False, nokkari_from=None):
        self.base_image_url = base_image_url
        self.background_image_url = background_image_url
        self.composited_image_url = composited_image_url
        self.caption = caption
        self.captured_time = datetime.fromtimestamp(float(captured_time))
        self.author_id = author_id
        self.weather = weather
        self.temperature = temperature
        self.longitude = longitude
        self.latitude = latitude
        self.comment = comment
        self.is_nokkari = is_nokkari
        self.nokkari_from = nokkari_from
        self.created_at = datetime.utcnow()
        
        
    
    
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

def is_user_login():
    return 'user_id' in session


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
        return make_error_json("ユーザ名は既に使用されています"), 403
        
        
    return make_error_json("予期しないエラーです"), 500

@app.route('/postInspiration', methods=['POST'])
def postInspiration():
    try:
        #if not is_user_login():
        #    return make_error_json("ログインする必要があります"), 403
        jsondata = request.json
        #jsondata["author_id"] = session["user_id"]
        jsondata["author_id"] = "1"
        inspiration = Inspiration(**jsondata)
        db.session.add(inspiration)
        db.session.commit()
        
        return make_data_json(dict()), 200
    except Exception as e:
        pass
    return make_error_json("予期しないエラーです"), 500

if __name__ == '__main__':
    app.run(port=5001)
