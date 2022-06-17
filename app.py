from logging import exception
from flask import Flask, request, abort, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt_identity, jwt_required, JWTManager
from werkzeug.security import generate_password_hash, check_password_hash
from config import ApplicationConfig
from models import db, User, Url, Visit, Document
import string
import random
import re


app = Flask(__name__)
app.config.from_object(ApplicationConfig)
jwt = JWTManager(app)

db.init_app(app)

with app.app_context():
    db.create_all()

# TODO: If a url has not been visited in a long time (> 6months) and was not craeted by a registered user, Allow it to be reassigned
# TODO: Endpoint to refresh token
# TODO: Endpoint to reset password
# TODO: Endpoint to edit user details

def generate_short_url(url):
    string_choice = string.ascii_letters + string.digits + '-'
    short_url = "".join([random.choice(string_choice) for _ in range(8)])

    while Url.query.filter_by(short_url=short_url).first():
        short_url = "".join([random.choice(string_choice) for _ in range(8)])
    return f"urely.com/{short_url}"


def validate_name(name):
    return type(name) == str and len(name) > 1

def validate_email(email):
    if not (type(email) == str and re.match("^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[-]?\w+[.]\w+$", email)):
        return None
    return True

def validate_password(password):
    return type(password) == str and len(password) >= 3

def validate_make_private(make_private):
    return make_private if type(make_private) == bool else None

def sanitize_short_url(url):
    if (not url) or type(url) != str: return None
    string_choice = string.ascii_letters + string.digits + '-'
    url = re.sub(r'^(http(s)?://)?(www.)?urely.com/', '', url, flags=re.IGNORECASE)
    if not any(ch in string_choice for ch in url):
        return None
    return f"urely.com/{url}"

def sanitize_long_url(url):
    if (not url) or type(url) != str: return None
    url = re.sub(r'^(http(s)?://)?(www.)?', 'https://', url, flags=re.IGNORECASE)
    if not (re.match("^((https?|ftp|file):\/\/)?[-A-Za-z0-9+&@#\/%?=~_|!:,.;]+[-A-Za-z0-9+&@#\/%=~_|]$", url) and ("." in url)):
        return None
    return url



@app.route("/")
def index():
    return "Welcome to URELY"


@app.route("/login", methods=["POST"])
def login():
    try:
        email = request.json.get("email", '')
        password = request.json.get("password", '')

        if not validate_email(email):
            return jsonify({"error": "invalid email"}), 400

        user = User.query.filter_by(email=email).first()

        if not (user and check_password_hash(user.password, password)):
            return jsonify({'error': 'invalid credentials'}), 401

        access = create_access_token(identity=user.id)
        refresh = create_refresh_token(identity=user.id)

    except Exception as e:
        return jsonify({'error': str(e)}), 400

    return  jsonify({
        'user': {
            'refesh': refresh,
            'access': access,
            'email': email
        }
    }), 200


@app.route("/register", methods=["POST"])
def register_user():
    try:
        first_name = request.json.get("first_name", None)
        last_name = request.json.get("last_name", None)
        email = request.json.get("email", None)
        password = request.json.get("password", None)

        if not (validate_name(first_name) and validate_name(last_name)):
            return jsonify({"error": "name should be string and more than one character long"}), 400

        if not validate_email(email):
            return jsonify({"error": "invalid email"}), 400

        if not validate_password(password):
            return jsonify({"error": "password must be minimum of 3 characters"}), 400

        user_exists = User.query.filter_by(email=email).first() is not None

        if user_exists:
            return jsonify({"error": "user already exists"}), 409

        new_user = User(first_name=first_name, last_name=last_name, email=email, password=generate_password_hash(password))
        db.session.add(new_user)
        db.session.commit()
        user_id = new_user.id

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

    finally:
        db.session.close()

    return jsonify({
        "id": user_id,
        "first_name": first_name,
        "last_name": last_name,
        "email": email
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


@app.route("/url/create", methods=["POST"])
def create_url():
    try:
        long_url = request.json.get("long_url", None)

        long_url = sanitize_long_url(long_url)

        if not long_url:
            return jsonify({"error": "missing or invalid url"}), 400

        url = Url.query.filter_by(long_url=long_url, is_private=False).first()

        if url:
            short_url = url.short_url
        else:
            short_url = generate_short_url(long_url)
            new_url = Url(long_url=long_url, short_url=short_url)
            db.session.add(new_url)
            db.session.commit()

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

    finally:
        db.session.close()

    return jsonify({
        'short_url': short_url
    }), 201


@app.route("/url/my-url/create", methods=["POST"])
@jwt_required()
def create_my_url():
    try:
        long_url = request.json.get("long_url", None)
        make_private = request.json.get("private", False)

        long_url = sanitize_long_url(long_url)
        make_private = validate_make_private(make_private)

        if not long_url:
            return jsonify({"error": "missing url"}), 400

        if make_private not in [True, False]:
            return jsonify({"error": "make_private should be boolean"}), 400

        user_id = get_jwt_identity()
        user = User.query.get(user_id)

        url = Url.query.filter_by(long_url=long_url, is_private=False).first()

        if url and not make_private:
            short_url = url.short_url
            if user not in url.users:
                url.users.append(user)
                db.session.commit()
        else:
            short_url = generate_short_url(long_url)
            new_url = Url(long_url=long_url, short_url=short_url, is_private=make_private, users=[user])
            db.session.add(new_url)
            db.session.commit()

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

    finally:
        db.session.close()

    return jsonify({
        'short_url': short_url
    }), 201


@app.route("/url/my-url/create-custom", methods=["POST"])
@jwt_required()
def create_my_url_alias():
    try:
        long_url = request.json.get("long_url", None)
        alias = request.json.get("alias", None)

        long_url = sanitize_long_url(long_url)
        my_short_url = sanitize_short_url(alias)

        if len(my_short_url) > 20 or len(my_short_url) < 13:
            return jsonify({"error": "length of alias should be in range 3 - 20"}), 400

        if not (long_url and my_short_url):
            return jsonify({"error": "missing or invalid url(s)"}), 400

        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        url = Url.query.filter_by(short_url=my_short_url).first()

        if url:
            return jsonify({'error': "url alias already taken"}), 409

        new_url = Url(long_url=long_url, short_url=my_short_url, is_private=True, users=[user])
        db.session.add(new_url)
        db.session.commit()

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

    finally:
        db.session.close()

    return jsonify({
        'short_url': my_short_url
    }), 201


@app.route("/url/visit")
def get_url():
    try:
        short_url = request.json.get("short_url", None)

        short_url = sanitize_short_url(short_url)

        if not short_url:
            return jsonify({"error": "no url provided"}), 400

        url = Url.query.filter_by(short_url=short_url).first()

        if not url:
            return jsonify({"error": "url does not exist"}), 404

        long_url = url.long_url
        visit = Visit()
        url.visits.append(visit)
        db.session.add(visit)
        db.session.commit()

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

    finally:
        db.session.close()

    return jsonify({
        'long_url': long_url
    }), 200


if __name__ == "__main__":
    app.run(debug=True)