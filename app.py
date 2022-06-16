from flask import Flask, request, abort, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt_identity, jwt_required, JWTManager
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from config import ApplicationConfig
from models import db, User, Url
import string
import random


app = Flask(__name__)
app.config.from_object(ApplicationConfig)
jwt = JWTManager(app)

db.init_app(app)

with app.app_context():
    db.create_all()


def generate_short_url(url):
    string_choice = string.ascii_letters + string.digits + '-'
    short_url = "".join([random.choice(string_choice) for _ in range(8)])
    return "urely.com/" + short_url


@app.route("/")
def index():
    return "URL Shortener"


@app.route("/login", methods=["POST"])
def login():
    email = request.json.get("email", '')
    password = request.json.get("password", '')

    user = User.query.filter_by(email=email).first()

    if user and check_password_hash(user.password, password):
        access = create_access_token(identity=user.id)
        refresh = create_refresh_token(identity=user.id)

        return  jsonify({
            'user': {
                'refesh': refresh,
                'access': access,
                'email': user.email
            }
        }), 200

    return jsonify({'error': 'Invalid credentials'}), 401



@app.route("/register", methods=["POST"])
def register_user():
    first_name = request.json.get("first_name", None)
    last_name = request.json.get("last_name", None)
    email = request.json.get("email", None)
    password = request.json.get("password", None)

    if not (first_name and last_name and email and password):
        return jsonify({"error": "Incomplete registration information"}), 400

    user_exists = User.query.filter_by(email=email).first() is not None

    if user_exists:
        return jsonify({"error": "User already exists"}), 409

    new_user = User(first_name=first_name, last_name=last_name, email=email, password=generate_password_hash(password))

    db.session.add(new_user)
    db.session.commit()

    return jsonify({
        "id": new_user.id,
        "first_name": new_user.first_name,
        "last_name": new_user.last_name,
        "email": new_user.email
    }), 201


@app.route("/user")
@jwt_required()
def get_user():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    return jsonify({
        "id": user.id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email
    }), 200


@app.route("/url", methods=["POST"])
def create_url():
    long_url = request.json.get("long_url", None)

    if not long_url:
        return jsonify({"error": "No url to shorten"}), 400

    url = Url.query.filter_by(long_url=long_url).first()

    if url:
        return jsonify({
            'short_url': url.short_url
        }), 201

    short_url = generate_short_url(long_url)
    new_url = Url(long_url=long_url, short_url=short_url)

    db.session.add(new_url)
    db.session.commit()

    return jsonify({
        'short_url': short_url
    }), 201
    

    

@app.route("/url/custom", methods=["POST"])
@jwt_required()
def create_my_url():
    long_url = request.json.get("long_url", None)
    custom_url = request.json.get("custom_url", None)

    if not (long_url and custom_url):
        return jsonify({"error": "missing url"}), 400

    url = Url.query.filter_by(long_url=long_url).first()

    if url:
        return jsonify({
            'short_url': url.short_url
        }), 201

    new_url = Url(long_url=long_url, short_url="urely.com/" + custom_url)

    db.session.add(new_url)
    db.session.commit()

    return jsonify({
        'short_url': new_url.short_url
    }), 201


@app.route("/url")
def get_url():
    short_url = request.json.get("short_url", None)

    if not short_url:
        return jsonify({"error": "no url provided"}), 400

    url = Url.query.filter_by(short_url=short_url).first()

    if not url:
        return jsonify({"error": "url does not exist"}), 404

    return jsonify({
        'short_url': url.long_url
    }), 200


if __name__ == "__main__":
    app.run(debug=True)