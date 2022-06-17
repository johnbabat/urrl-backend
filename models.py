from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from uuid import uuid4

db = SQLAlchemy()

def get_uuid():
    return uuid4().hex


user_urls = db.Table('user_urls',
    db.Column('user_id', db.String(32), db.ForeignKey('users.id')),
    db.Column('url_id', db.String(32), db.ForeignKey('urls.id')),
)

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.String(32), primary_key=True, unique=True, default=get_uuid)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(345), unique=True)
    password = db.Column(db.Text(), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    documents = db.relationship('Document', backref='user', lazy='select')
    urls = db.relationship('Url', secondary=user_urls, backref='users', lazy='select')
    
    def __repr__(self):
        return self.first_name + ' ' + self.last_name + ' -> ' + self.id


class Url(db.Model):
    __tablename__ = "urls"
    id = db.Column(db.String(32), primary_key=True, unique=True, default=get_uuid)
    short_url = db.Column(db.String(30), unique=True)
    long_url = db.Column(db.Text())
    is_private = db.Column(db.Boolean(), default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    visits = db.relationship('Visit', backref='url', lazy='select')

    def __repr__(self):
        return self.short_url + ' - ' + self.long_url + ' -> ' + self.id


class Document(db.Model):
    __tablename__ = "documents"
    id = db.Column(db.String(32), primary_key=True, unique=True, default=get_uuid)
    user_id = db.Column(db.String(32), db.ForeignKey('users.id'), nullable=False)
    text = db.Column(db.Text(), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    def __repr__(self):
        return self.text + ' -> ' + self.id


class Visit(db.Model):
    __tablename__ = "visits"
    id = db.Column(db.String(32), primary_key=True, unique=True, default=get_uuid)
    url_id = db.Column(db.String(32), db.ForeignKey('urls.id'), nullable=False)
    time = db.Column(db.DateTime, default=datetime.utcnow)