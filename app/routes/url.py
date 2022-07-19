from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from app.models import db, User, Url, Visit
from app.utils.helpers import sanitize_long_url, sanitize_short_url, generate_short_url, validate_make_private


url = Blueprint("url", __name__, url_prefix="/api/v1/url")


@url.get("/visit/")
def get_url():
    try:
        args = request.args
        alias = args.get("alias", default=None, type=str)

        short_url = sanitize_short_url(alias)

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



@url.post("/create")
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

    return jsonify({ 'short_url': short_url }), 201



@url.post("/private/create")
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



@url.post("/private/create-custom")
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


@url.delete("/delete/<url_id>")
@jwt_required()
def delete_url(url_id):
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)

        url = Url.query.get(url_id)

        if user in url.users:
            url.users.remove(user)

        db.session.commit()

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

    finally:
        db.session.close()

    return jsonify({ 'url_id': url_id }), 200