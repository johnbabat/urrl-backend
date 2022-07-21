import os
import base64
from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import func, desc, asc
from api.models import db, User, Url, Visit, Document
from api.utils.helpers import get_file_extension, validate_password, validate_name, validate_email, number_to_month


user = Blueprint("user", __name__, url_prefix="/api/v1/user")


@user.get("/")
@jwt_required()
def get_user():
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

    finally:
        db.session.close()

    return jsonify({
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "avatar": base64_avatar
    }), 200



@user.post("/")
@jwt_required()
def post_user():
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

    finally:
        db.session.close()

    return jsonify({
        "id": user_id,
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "avatar": base64_avatar
    }), 201



@user.get("/urls")
@jwt_required()
def get_user_urls():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)

        urls = user.urls
        user_urls = [{
                        "id": url.id,
                        "short_url": url.short_url, 
                        "long_url": url.long_url,
                        "alias": url.short_url[10:],
                        "private": url.is_private 
                    } for url in urls]

        url_pie = db.session.query(Url, func.count(Url.visits))\
                .filter(Url.users.contains(user))\
                .outerjoin(Visit, Url.id==Visit.url_id)\
                .group_by(Url).order_by(desc(func.count(Url.visits)))\
                .limit(5)\
                .all()

        sum_urls = sum([stat[1] for stat in url_pie])

        url_stats = [{
                    'x': stat[0].short_url,
                    'y': stat[1],
                    'text': (str(round((stat[1]/sum_urls * 100), 1)) + '%') if sum_urls > 0 else '0%' 
                } for stat in url_pie]

    except Exception as e:
        return jsonify({'error': str(e)}), 400

    finally:
        db.session.close()

    return jsonify({
        'urls': user_urls,
        'top_stats': url_stats
    }), 200



@user.get("/documents")
@jwt_required()
def get_user_documents():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)

        documents = sorted(user.documents, key=lambda x: x.created_at)[::-1]
        user_documents = [{
                        "id": document.id,
                        "title": document.title, 
                        "plain_text": document.plain_text,
                        "private": document.is_private 
                    } for document in documents]

        document_pie = db.session.query(Document, func.count(Document.visits))\
                    .filter(Document.user == user)\
                    .outerjoin(Visit, Document.id==Visit.document_id)\
                    .group_by(Document)\
                    .order_by(desc(func.count(Document.visits)))\
                    .limit(5)\
                    .all()

        sum_documents = sum([stat[1] for stat in document_pie])

        document_top_stats = [{
                                'x': stat[0].title,
                                'y': stat[1],
                                'text': (str(round((stat[1]/sum_documents * 100), 1)) + '%')if sum_documents > 0 else '0%'
                            } for stat in document_pie]

    except Exception as e:
        return jsonify({'error': str(e)}), 400

    finally:
        db.session.close()

    return jsonify({
        'documents': user_documents,
        'top_stats': document_top_stats
    }), 200



@user.post("/edit")
@jwt_required()
def edit_user():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)

        avatar = request.files.get("file", None)
        first_name = request.form.get("first_name", None)
        last_name = request.form.get("last_name", None)
        email = request.form.get("email", None)

        if not (validate_name(first_name) and validate_name(last_name)):
            return jsonify({ "error": "name should be string and more than one character long" }), 400

        if not validate_email(email):
            return jsonify({ "error": "invalid email" }), 400

        if avatar:
            # filename = secure_filename(user_id + avatar.filename)
            file_extension = get_file_extension(avatar.filename)
            filename = secure_filename(user_id + file_extension)
            avatar.save(os.path.join('data/imgs', filename))

            with open(os.path.join('data/imgs', filename), 'rb') as binary_file:
                binary_file_data = binary_file.read()
                base64_encoded_data = base64.b64encode(binary_file_data)
                base64_avatar = base64_encoded_data.decode('utf-8')
        else:
            base64_avatar = ''
        
        user_with_email = User.query.filter_by(email=email).first()

        if user_with_email and (user_with_email.id != user.id):
            return jsonify({ "error": "email already in use by another user" }), 409

        if avatar:
            prev_avatar = user.avatar
            if prev_avatar and os.path.exists(prev_avatar):
                os.remove(prev_avatar)
            user.avatar = filename

        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        db.session.commit()

    except Exception as e:
        db.session.rollback()
        return jsonify({ 'error': str(e) }), 400
    
    finally:
        db.session.close()

    return jsonify({
        "id": user_id,
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "avatar": base64_avatar
    }), 201



@user.route("/user/change-password", methods=["PATCH"])
@jwt_required()
def change_password():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)

        old_password = request.json.get("old_password", None)
        new_password = request.json.get("new_password", None)

        if not check_password_hash(user.password, old_password):
            return jsonify({ 'error': 'invalid credentials' }), 401

        if not (validate_password(new_password) and validate_password(old_password)):
            return jsonify({ "error": "password must be minimum of 3 characters" }), 400
        
        user.password = generate_password_hash(new_password)
        db.session.commit()

    except Exception as e:
        db.session.rollback()
        return jsonify({ 'error': str(e) }), 400

    finally:
        db.session.close()

    return jsonify({ 'success': True }), 201



@user.get("/stats")
@jwt_required()
def get_user_stats():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)

        one_year_ago = datetime.now() - timedelta(days=365)

        url_grouped = db.session.query(func.date_part('YEAR', func.date(Visit.time)), func.date_part('MONTH', func.date(Visit.time)), func.count(Visit.url_id))\
                        .join(Url)\
                        .filter(Url.users.contains(user))\
                        .filter(Visit.time.between(one_year_ago, datetime.utcnow()))\
                        .group_by(func.date_part('YEAR', func.date(Visit.time)), func.date_part('MONTH', func.date(Visit.time)))\
                        .order_by(asc(func.date_part('YEAR', func.date(Visit.time))), asc(func.date_part('MONTH', func.date(Visit.time))))\
                        .all()
        document_grouped = db.session.query(func.date_part('YEAR', func.date(Visit.time)), func.date_part('MONTH', func.date(Visit.time)), func.count(Visit.document_id))\
                            .join(Document)\
                            .filter(Document.user == user)\
                            .filter(Visit.time.between(one_year_ago, datetime.utcnow()))\
                            .group_by(func.date_part('YEAR', func.date(Visit.time)), func.date_part('MONTH', func.date(Visit.time)))\
                            .order_by(asc(func.date_part('YEAR', func.date(Visit.time))), asc(func.date_part('MONTH', func.date(Visit.time))))\
                            .all()

        stacked_url = [{
                        'x': number_to_month[int(stat[1])],
                        'y': stat[2]
                    } for stat in url_grouped]
        stacked_document = [{
                        'x': number_to_month[int(stat[1])],
                        'y': stat[2]
                    } for stat in document_grouped]

        line_url = [{
                        'x': [int(stat[0]), int(stat[1])],
                        'y': stat[2]
                    } for stat in url_grouped]
        line_document = [{
                        'x': [int(stat[0]), int(stat[1])],
                        'y': stat[2]
                    } for stat in document_grouped]


        url_pie = db.session.query(Url, func.count(Url.visits))\
                    .filter(Url.users.contains(user))\
                    .outerjoin(Visit, Url.id==Visit.url_id)\
                    .group_by(Url)\
                    .order_by(desc(func.count(Url.visits)))\
                    .limit(5)\
                    .all()
        document_pie = db.session.query(Document, func.count(Document.visits))\
                    .filter(Document.user == user)\
                    .outerjoin(Visit, Document.id==Visit.document_id)\
                    .group_by(Document)\
                    .order_by(desc(func.count(Document.visits)))\
                    .limit(5)\
                    .all()

        sum_urls = sum([stat[1] for stat in url_pie])
        sum_documents = sum([stat[1] for stat in document_pie])

        url_top_stats = [{
                        'x': stat[0].short_url,
                        'y': stat[1],
                        'text': (str(round((stat[1]/sum_urls * 100), 1)) + '%') if sum_urls > 0 else '0%'
                    } for stat in url_pie]
        document_top_stats = [{
                                'x': stat[0].title,
                                'y': stat[1],
                                'text': (str(round((stat[1]/sum_documents * 100), 1)) + '%')if sum_documents > 0 else '0%'
                            } for stat in document_pie]
    
    except Exception as e:
        db.session.rollback()
        return jsonify({ 'error': str(e) }), 400

    finally:
        db.session.close()
    
    return jsonify({
        'url_pie': url_top_stats,
        'document_pie': document_top_stats,
        'stacked': [stacked_url, stacked_document],
        'line': [line_url, line_document]
    }), 200