from pydoc import doc
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from api.models import db, User, Visit, Document


document = Blueprint("document", __name__, url_prefix="/api/v1/document")


@document.get("/id/<document_id>")
@jwt_required()
def get_document(document_id):
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)

        document = Document.query.get(document_id)

        if not document:
            return jsonify({"error": "document not found"}), 404

        if document.is_private:
            if user not in document.users_sharing:
                jsonify({"error": "restricted access"}), 403

        visit = Visit()
        document.visits.append(visit)
        db.session.add(visit)
        db.session.commit()

        id = document.id
        title = document.title
        html_text = document.html_text
        users_sharing = [current_user.email for current_user in document.users_sharing]
        private = document.is_private

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

    finally:
        db.session.close()
        
    return jsonify({
        "id": id,
        "title": title,
        "html_text": html_text,
        "users_sharing": users_sharing,
        "private": private
    }), 200
        


@document.post("/create")
@jwt_required()
def create_document():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)

        title = request.json.get("title", None)
        html_text = request.json.get("html_text", None)
        plain_text = request.json.get("plain_text", None)
        is_private = request.json.get("is_private", False)

        if not (title and html_text and plain_text):
            return jsonify({"error": "missing or invalid title or content"}), 400

        document = Document(title=title, html_text=html_text, plain_text=plain_text, is_private=is_private, user=user)
        db.session.add(document)
        db.session.commit()
        doc_id = document.id

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

    finally:
        db.session.close()

    return jsonify({ 'id': doc_id }), 201



@document.route("/edit", methods=["PATCH"])
@jwt_required()
def edit_document():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)

        document_id = request.json.get("id", None)
        title = request.json.get("title", None)
        html_text = request.json.get("html_text", None)
        plain_text = request.json.get("plain_text", None)
        is_private = request.json.get("is_private", None)

        if not document_id:
            return jsonify({"error": "document not found"}), 404

        document = Document.query.get(document_id)

        if document.is_private:
            if user != document.user and (user not in document.users_sharing):
                jsonify({"error": "restricted access"}), 403


        if title:
            document.title = title
        if html_text and plain_text:
            document.html_text = html_text
            document.plain_text = plain_text
        if is_private is not None:
            document.is_private = is_private

        db.session.commit()

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

    finally:
        db.session.close()

    return jsonify({ 'message': "success" }), 201



@document.route("/edit/sharing", methods=["PATCH"])
@jwt_required()
def edit_document_sharing():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)

        user_email = request.json.get("user_email", None)
        add_user = request.json.get("add_user", None)
        document_id = request.json.get("id", None)

        if (add_user is None) or (user_email is None) or (document_id is None):
            return jsonify({"error": "incomplete edit information"}), 400

        document = Document.query.get(document_id)

        if document.is_private:
            if user != document.user and (user not in document.users_sharing):
                return jsonify({"error": "restricted access"}), 403

        if not add_user:
            user_to_remove = User.query.filter_by(email=user_email).first()
            if user_to_remove in document.users_sharing:
                document.users_sharing.remove(user_to_remove)
        else:
            user_to_add = User.query.filter_by(email=user_email).first()

            if not user_to_add:
                return jsonify({"error": "no user with given email"}), 404

            if user_to_add not in document.users_sharing:
                document.users_sharing.append(user_to_add)

        db.session.commit()
        users_sharing = [current_user.email for current_user in document.users_sharing]

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

    finally:
        db.session.close()

    return jsonify({ 'users_sharing': users_sharing }), 201



@document.delete("/delete/<document_id>")
@jwt_required()
def delete_document(document_id):
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)

        document = Document.query.get(document_id)

        if document.user == user:
            db.session.delete(document)

        db.session.commit()

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

    finally:
        db.session.close()

    return jsonify({ 'document_id': document_id }), 200