# coding: utf-8
from __future__ import unicode_literals

from flask import Flask, request, jsonify, session
from flask.json import JSONEncoder
from flask_sqlalchemy import SQLAlchemy
import hashlib
from datetime import datetime
import sqlite3
from os.path import abspath, dirname, join
import time


# global variables
app = Flask('inspix')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + join(dirname(abspath(__file__)), 'database.db')
app.config['JSON_AS_ASCII'] = False 
app.secret_key = 'INSPIX_VULNERABLE_SECRET'

db = SQLAlchemy(app)

# constants
default_image_url = 'https://theoldmoon0602.tk/bin/theoldmoon0602.png'
password_salt = 'INSPIX_VULNERABLE_SALT'

followers = db.Table('followers', 
                           db.Column('from_id', db.Integer, db.ForeignKey('users.id'), nullable=False),
                           db.Column('to_id', db.Integer, db.ForeignKey('users.id'), nullable=False))

kininaru_relation = db.Table('kininaru',
                    db.Column('from_id', db.Integer, db.ForeignKey('users.id'), nullable=False),
                    db.Column('to_id', db.Integer, db.ForeignKey('inspirations.id'), nullable=False))

def to_timestamp(dt):
    return int(time.mktime(dt.timetuple()))

# Models
class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False, unique=True)
    password = db.Column(db.String, nullable=False)
    created_at = db.Column(db.DateTime)
    face_image = db.Column(db.String)
    inspirations = db.relationship('Inspiration', backref='author', lazy='dynamic')
    followed = db.relationship('User', secondary= followers,
                                primaryjoin=(id==followers.c.from_id),
                                secondaryjoin=(id==followers.c.to_id),
                                backref=db.backref('followers', lazy='dynamic'),
                                lazy='dynamic')
    kininari = db.relationship('Inspiration', secondary= kininaru_relation, backref='kininatteru', lazy='dynamic')
    
    def __init__(self, name, password, face_image=default_image_url):
        self.name = name
        self.face_image = face_image
        self.password = self.generate_password(password)
        self.created_at = datetime.utcnow()
    
    def generate_password(self, password):
        return hashlib.sha256(password_salt+password).hexdigest()
        
    def check_password(self, password):
        return self.password == self.generate_password(password)
    
    def is_following_user(self, user):
        return self.followed.filter(user.id == followers.c.to_id).count() > 0
    
    def follow_user(self, user):
        if not self.is_following_user(user):
            self.followed.append(user)
    
    def unfollow_user(self, user):
        if self.is_following_user(user):
            self.followed.remove(user)
            
    def is_kininatteru(self, inspiration):
        return self.kininari.filter(Inspiration.id == kininaru_relation.c.to_id).count() > 0
    
    def kininaru(self, inspiration):
        if not self.is_kininatteru(inspiration):
            self.kininari.append(inspiration)
            
    def unkininaru(self, inspiration):
        if self.is_kininatteru(inspiration):
            self.kininari.remove(inspiration)
            
    def user_digest(self):
        return {
            "id": self.id,
            "name": self.name,
            "thumbnail_image": self.face_image
        }
        
        
            
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
    nokkari_from_id = db.Column(db.Integer, db.ForeignKey("inspirations.id"))
    nokkari_from = db.relationship('Inspiration', uselist=False)
    created_at = db.Column(db.DateTime)
    
    def __init__(self, base_image_url, background_image_url, composited_image_url, caption, captured_time, author_id,
                 weather=None, temperature=None, longitude=None, latitude=None,
                 comment="", nokkari_from_id=None):
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
        self.is_nokkari = False
        self.created_at = datetime.utcnow()
        if nokkari_from_id:
            self.is_nokkari = True
            self.nokkari_from_id = nokkari_from_id
            self.nokkari_from = Inspiration.query.filter(Inspiration.id == nokkari_from_id).first()
        
    def jsonable(self):
        """
        return jsonifiable object
        """
        retdict = {
            'base_image_url': self.base_image_url,
            'background_image_url': self.background_image_url,
            'composited_image_url': self.composited_image_url,
            'caption': self.caption,
            'captured_time': to_timestamp(self.captured_time),
            'created_at': to_timestamp(self.created_at),
            'author': self.author.user_digest()
        }
        
        if self.weather:
            retdict['weather'] = self.weather
        if self.temperature:
            retdict['temperature'] = self.temperature
        if self.longitude:
            retdict['longitude'] = self.longitude
        if self.latitude:
            retdict['latitude'] = self.latitude
        
        if self.is_nokkari:
            retdict['nokkari_from'] = self.nokkari_from.jsonable()
        
        return retdict
        
        
    
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

def get_login_user():
    return User.query.filter(User.id==1).first()
    # return User.query.filter(id == session['user_id']).first()

@app.route('/testlogin', methods=['GET'])
def test_login():
    return make_data_json({'is_login': is_user_login()}), 200

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

@app.route('/kininaru', methods=['PUT', 'DELETE'])
def kininaru():
    try:
        #if not is_user_login():
        #    return make_error_json("ログインする必要があります"), 403
        jsondata = request.json
        #jsondata["author_id"] = session["user_id"]
        user = get_login_user()
        to_inspiration = Inspiration.query.filter(Inspiration.id==jsondata['inspiration_id']).first()
        
        if request.method == 'PUT':
            user.kininaru(to_inspiration)
            db.session.commit()
            return make_data_json({}), 200        
        elif request.method == 'DELETE':
            user.unkininaru(to_inspiration)
            db.session.commit()
            return make_data_json({}), 200
    except Exception as e:
        pass
    
    return make_error_json('予期しないエラーです'), 500


@app.route('/follow', methods=['PUT', 'DELETE'])
def follow():
    try:
        #if not is_user_login():
        #    return make_error_json("ログインする必要があります"), 403
        jsondata = request.json
        #jsondata["author_id"] = session["user_id"]
        user = get_login_user()
        to_user = User.query.filter(User.id==jsondata['user_id']).first()
        
        if user.id == to_user.id:
            return make_error_json("予期しないエラーです"), 500
        
        if request.method == 'PUT':
            user.follow_user(to_user)
            db.session.commit()
            return make_data_json({}), 200        
        elif request.method == 'DELETE':
            user.unfollow_user(to_user)
            db.session.commit()
            return make_data_json({}), 200
    except Exception as e:
        pass
    
    return make_error_json('予期しないエラーです'), 500

@app.route('/followTimeline', methods=['GET'])
def followTimeline():
    #if not is_user_login():
    #    return make_error_json("ログインする必要があります"), 403
    #jsondata = request.json
    #jsondata["author_id"] = session["user_id"]
    user = get_login_user() #type: User
    followed_ids = [followed.id for followed in user.followed]
    inspirations = Inspiration.query.filter(Inspiration.author_id.in_(followed_ids)).order_by(Inspiration.created_at.desc()).all()
    return make_data_json({"Inspirations": [v.jsonable() for v in inspirations]}), 200
    

if __name__ == '__main__':
    app.run(port=5001)
