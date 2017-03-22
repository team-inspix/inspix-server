# coding: utf-8
from __future__ import unicode_literals

from flask import Flask, request, jsonify, session
from flask.json import JSONEncoder
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import sqlite3
from os.path import abspath, dirname, join
import time
import random
import string
import base64
import hashlib
import requests
import json
import traceback
import os



# global variables
app = Flask('inspix')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.environ["INSPIX_DB"]
app.config['JSON_AS_ASCII'] = False 
app.secret_key = os.environ.get("INSPIX_SECRET", 'INSPIX_VULNERABLE_SECRET')

db = SQLAlchemy(app)

bluemix_user_password = os.environ["INSPIX_BLUEMIX_USERNAME"] + ":" + os.environ["INSPIX_BLUEMIX_PASSWORD"]

def errorlog(e):
    f = join(dirname(__file__), "error.log")
    open(f, "a").write(e.message+"::"+traceback.format_exc()+"\n")

# constants
default_image_url = os.environ.get("INSPIX_DEFAULT_FACE", "https://raw.githubusercontent.com/team-inspix/inspix-server/master/theoldmoon0602.png")
password_salt = os.environ.get("INSPIX_PASSWORD_SALT", 'INSPIX_VULNERABLE_SALT')

followers = db.Table('followers', 
                           db.Column('from_id', db.Integer, db.ForeignKey('users.id'), nullable=False),
                           db.Column('to_id', db.Integer, db.ForeignKey('users.id'), nullable=False))

kininaru_relation = db.Table('kininaru',
                    db.Column('from_id', db.Integer, db.ForeignKey('users.id'), nullable=False),
                    db.Column('to_id', db.Integer, db.ForeignKey('inspirations.id'), nullable=False))

def to_timestamp(dt):
    return int(time.mktime(dt.timetuple()))

def getWeatherData(longitude, latitude):
    global bluemix_user_password
    url = "https://"+bluemix_user_password+"@twcservice.mybluemix.net:443/api/weather/v1/geocode/{}/{}/forecast/hourly/48hour.json?units=m".format(latitude, longitude)
    
    r = requests.get(url)
    data = json.loads(r.text)
    
    return getDaystateString(data["forecasts"][0]), getTemperature(data["forecasts"][0])
    
def getTemperature(daystate):
    return int(daystate["temp"])

def getDaystateString(daystate):
    d = daystate["phrase_32char"]
    if "Clear" in d:
        return "sunny"
    if "Sunny" in d:
        return "sunny"
    if "Cloudy" in d:
        return "cloudy"
    if "Rainy" in d:
        return "rainy"
    return ""



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
    kininari = db.relationship('Inspiration', secondary=kininaru_relation,
                               backref=db.backref('kininarare', lazy='dynamic'),
                               lazy='dynamic')
    
    def __init__(self, name, password, face_image=default_image_url, **kwargs):
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
        # TOO TOO LATE! TOO TOO LATE! TOO TOO P P P ComeOn...
        return inspiration.id in [v.id for v in self.kininari.all()]
        # return self.kininari.filter(Inspiration.id == kininaru_relation.c.to_id).count() > 0
    
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
    title = db.Column(db.String)
    
    comment = db.Column(db.String)
    is_nokkari = db.Column(db.Boolean)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    nokkari_from_id = db.Column(db.Integer, db.ForeignKey("inspirations.id"))
    nokkari_from = db.relationship('Inspiration', backref='nokkarare', remote_side=[id])
    created_at = db.Column(db.DateTime)
    
    def __init__(self, background_image_url, composited_image_url, caption, author_id,
                 base_image_url="",
                 title=None,
                 captured_time=None, weather=None, temperature=None, longitude=None, latitude=None,
                 nokkari_from=None, **kwargs):
        self.base_image_url = base_image_url
        self.background_image_url = background_image_url
        self.composited_image_url = composited_image_url
        self.caption = caption
        if captured_time:
            self.captured_time = datetime.fromtimestamp(float(captured_time))
        else:
            self.captured_time = None
            
        self.author_id = author_id
        self.weather = weather
        self.temperature = temperature
        if longitude:
            self.longitude = float(longitude)
        if latitude:
            self.latitude = float(latitude)
        if not self.weather and self.longitude and self.latitude:
            try:
                self.weather, self.temperature = getWeatherData(longitude=self.longitude, latitude=self.latitude)
            except Exception as e:
                errorlog(e)
            
        self.created_at = datetime.utcnow()
        self.title = title
        
        self.is_nokkari = False
        
        if nokkari_from:
            self.is_nokkari = True
            self.nokkari_from = nokkari_from
        
    def jsonable(self):
        """
        return jsonifiable object
        """
        retdict = {
            'id': self.id,
            'base_image_url': self.base_image_url or "",
            'background_image_url': self.background_image_url or "",
            'composited_image_url': self.composited_image_url or "",
            'caption': self.caption,
            'created_at': to_timestamp(self.created_at),
            'author': self.author.user_digest()
        }
        
        if self.captured_time:
            retdict['captured_time'] = to_timestamp(self.captured_time)
        
        if self.weather:
            retdict['weather'] = self.weather
        if self.temperature:
            retdict['temperature'] = self.temperature
        if self.longitude:
            retdict['longitude'] = self.longitude
        if self.latitude:
            retdict['latitude'] = self.latitude
        if self.title:
            retdict['title'] = self.title
        else:
            retdict['title'] = ""
            
        retdict['nokkarare'] = [i.jsonable() for i in self.nokkarare]
            
        retdict['kininatteru'] = get_login_user().is_kininatteru(self)
        retdict['kininaru_users'] = [u.user_digest() for u in self.kininarare]
        retdict['kininaru_count'] = self.kininarare.count()
        
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
    # return User.query.filter(User.id == session['user_id']).first()


# impls
def login_impl(jsondata):
    user = User.query.filter_by(id=jsondata['id']).first()
    
    if not user.check_password(jsondata['password']):
        return make_error_json("ログインに失敗しました"), 403
    
    session['user_id'] = user.id
    return True

def register_impl(jsondata):
    user = User(jsondata['name'],  jsondata['password'])
    db.session.add(user)
    db.session.commit()

    return user.id

def postInspiration_impl(jsondata):  
    inspiration = Inspiration(**jsondata)
    db.session.add(inspiration)
    db.session.commit()

def nokkari_impl(jsondata):
    nokkari_from = Inspiration.query.filter(Inspiration.id == jsondata["nokkari_from_id"]).first() #type: Inspiration
    jsondata["nokkari_from"] = nokkari_from
    jsondata["background_image_url"] = nokkari_from.background_image_url
    jsondata.pop("nokkari_from_id", None)
    inspiration = Inspiration(**jsondata)
    db.session.add(inspiration)
    db.session.commit()    

def userTimeline_impl(jsondata):
    user_id = jsondata['user_id']
    page = jsondata['page']
    inspirations = Inspiration.query.filter(Inspiration.author_id == user_id).\
        filter(Inspiration.is_nokkari == False).\
        order_by(Inspiration.created_at.desc()).\
        paginate(page=int(page), per_page=100, error_out=False).items
    user = User.query.filter(User.id == user_id).first() # type: User
    digest = user.user_digest()
    digest["following"] = get_login_user().is_following_user(user)
    return inspirations, digest

def randstr(l):
    return "".join([random.choice(string.ascii_letters) for i in range(l)])

def imageUpload_impl(jsondata):
    bindir = join(dirname(abspath(__file__)), "bin")
    name = randstr(20)+"."+jsondata["ext"]
    fname = join(bindir, name)
    with open(fname, 'wb') as f:
        f.write(base64.b64decode(jsondata["bin"]))
    return join(request.url_root, "bin",  name)

def followTimeline_impl(jsondata):
    user = get_login_user() #type: User
    followed_ids = [followed.id for followed in user.followed]
    inspirations = Inspiration.query.filter(
        Inspiration.author_id.in_(followed_ids)).\
        order_by(Inspiration.created_at.desc()).\
        paginate(page=int(jsondata["page"]), per_page=100, error_out=False).items
    return inspirations


# 
#def pickupTimeline_impl(jsondata):
    #Inspiration.query.filter(Inspiration.is_nokkari==False).\
        #order_by(func.count(Inspiration.

def pickupTimeline_impl(jsondata):
    inspirations = Inspiration.query.order_by(Inspiration.created_at.desc()).\
    paginate(page=int(jsondata["page"]), per_page=100, error_out=False).items
    return inspirations

def kininaruList_impl(jsondata):
    me = get_login_user() # type: User
    kininaruList = me.kininari.order_by(Inspiration.created_at.desc()).\
        paginate(page=int(jsondata["page"]), per_page=10, error_out=False).items
    return kininaruList

# route

@app.route('/testlogin', methods=['GET'])
def test_login():
    return make_data_json({'is_login': is_user_login()}), 200

@app.route('/login', methods=['POST'])
def login():
    try:
        is_logined = login_impl(request.json)
        
        return make_data_json({"result": is_logined}), 200
        
    except Exception as e:
        errorlog(e)
    return make_error_json("ログインに失敗しました"), 403            

@app.route('/register', methods=['POST'])
def register():
    try:
        user_id = register_impl(request.json)
        return make_data_json({"id": user_id}), 201
    except Exception as e:
        errorlog(e)
        return make_error_json("ユーザ名は既に使用されています"), 403
        
    return make_error_json("予期しないエラーです"), 500

@app.route('/postInspiration', methods=['POST'])
def postInspiration():
    try:
        if not is_user_login():
            return make_error_json("ログインする必要があります"), 403
        jsondata = request.json
        jsondata["author_id"] = session["user_id"]
        postInspiration_impl(jsondata)        
        return make_data_json(dict()), 200
    except Exception as e:
        errorlog(e)
    return make_error_json("予期しないエラーです"), 500

@app.route('/nokkari', methods=['POST'])
def nokkari():
    try:
        if not is_user_login():
            return make_error_json("ログインする必要があります"), 403
        jsondata = request.json
        jsondata["author_id"] = session["user_id"]
        
        nokkari_impl(jsondata)
        return make_data_json({}), 200
    except Exception as e:
        errorlog(e)
    return make_error_json('予期しないエラーです'), 500

def array_jsonable(arr):
    return [v.jsonable() for v in arr]

@app.route('/userTimeline', methods=['GET'])
def userTimeline():
    try:
        jsondata = request.json
        inspitraions, user = userTimeline_impl(jsondata)
        inspitraions = array_jsonable(inspirations)
        
        return make_data_json({"user": user, "Inspirations": inspitraions}), 200
    except Exception as e:
        errorlog(e)
    return make_error_json('予期しないエラーです'), 500

@app.route('/kininaru', methods=['PUT', 'DELETE'])
def kininaru():
    try:
        if not is_user_login():
            return make_error_json("ログインする必要があります"), 403
        jsondata = request.json
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
        errorlog(e)
    
    return make_error_json('予期しないエラーです'), 500

@app.route('/follow', methods=['PUT', 'DELETE'])
def follow():
    try:
        if not is_user_login():
            return make_error_json("ログインする必要があります"), 403
        jsondata = request.json
        jsondata["author_id"] = session["user_id"]
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
        errorlog(e)
    
    return make_error_json('予期しないエラーです'), 500



@app.route('/followTimeline', methods=['GET'])
def followTimeline():
    try:
        if not is_user_login():
            return make_error_json("ログインする必要があります"), 403
        inspirations = array_jsonable(followTimeline_impl(request.json))
        
        return make_data_json({"Inspirations": inspirations}), 200
    except Exception as e:
        errorlog(e)
    
    return make_error_json('予期しないエラーです'), 500   

@app.route('/pickupTimeline', methods=['GET'])
def pickupTimeline():
    try:
        inspirations = array_jsonable(pickupTimeline_impl(request.json))
        return make_data_json({"Inspirations": inspirations}), 200
    except Exception as e:
        errorlog(e)
    return make_error_json('予期しないエラーです'), 500 

    
@app.route('/imageUpload', methods=['PUT'])
def imageUpload():
    """ this method is very very insecure """
    try:
        fileUrl = imageUpload_impl(request.json)
        return make_data_json({"file_url": fileUrl}), 201
    except Exception as e:
        errorlog(e)
    return make_error_json('予期しないエラーです'), 500

@app.route('/kininaruList', methods=['GET'])
def kininaruList():
    try:
        inspirations = array_jsonable(kininaruList_impl(request.json))
        return make_data_json({"Inspirations": inspirations})
    except Exception as e:
        errorlog(e)
    return make_error_json('予期しないエラーです'), 500

if __name__ == '__main__':
    app.run()
