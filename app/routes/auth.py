import os
import base64
from flask import Blueprint, jsonify, request, make_response
from flask_cors import cross_origin
from flask_jwt_extended import create_access_token, get_jwt_identity, create_refresh_token, set_access_cookies, set_refresh_cookies, unset_jwt_cookies, jwt_required
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import db, User
from app.utils.helpers import validate_password, validate_name, validate_email


auth = Blueprint("auth", __name__, url_prefix="/api/v1/auth")


@auth.post("/login")
def login():
    try:
        email = request.json.get("email", '')
        password = request.json.get("password", '')

        if not validate_email(email):
            return jsonify({"error": "invalid email"}), 400

        user = User.query.filter_by(email=email).first()

        if not (user and check_password_hash(user.password, password)):
            return jsonify({'error': 'invalid credentials'}), 401

        first_name = user.first_name
        last_name = user.last_name
        email = user.email
        avatar = user.avatar
        if avatar:
            with open(os.path.join('data/imgs', avatar), 'rb') as binary_file:
                binary_file_data = binary_file.read()
                base64_encoded_data = base64.b64encode(binary_file_data)
                base64_avatar = base64_encoded_data.decode('utf-8')
        else:
            base64_avatar = ''

        access = create_access_token(identity=user.id)
        refresh = create_refresh_token(identity=user.id)

    except Exception as e:
        return jsonify({'error': str(e)}), 400

    response = make_response(jsonify({
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "avatar": base64_avatar
    }), 200)

    set_access_cookies(response, access)
    set_refresh_cookies(response, refresh)

    return response



@auth.post("/register")
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



@auth.get("/logout")
def logout():
    response = make_response(jsonify({'message': 'logged out'}), 200)
    unset_jwt_cookies(response)

    return response



@auth.get('/validate')
@jwt_required()
def validate():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    try:
        first_name = user.first_name
        last_name = user.last_name
        email = user.email
        avatar = user.avatar
        if avatar:
            with open(os.path.join('data/imgs', avatar), 'rb') as binary_file:
                binary_file_data = binary_file.read()
                base64_encoded_data = base64.b64encode(binary_file_data)
                base64_avatar = base64_encoded_data.decode('utf-8')
        else:
            base64_avatar = ''

    except Exception as e:
        return jsonify({'error': str(e)}), 400

    return jsonify({
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "avatar": base64_avatar,
        "success": True
    }), 200
