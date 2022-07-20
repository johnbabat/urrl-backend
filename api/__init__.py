import os
from flask import Flask, jsonify, make_response, redirect, url_for
from flask_jwt_extended import JWTManager, get_jwt_identity, jwt_required, create_access_token, set_access_cookies, unset_access_cookies
from flask_cors import CORS
from api.config import ApplicationConfig
from api.models import db, migrate
from api.utils import stats

from api.routes.auth import auth
from api.routes.user import user
from api.routes.url import url
from api.routes.document import document


# TODO: If a url has not been visited in a long time (> 6months) and was not craeted by a registered user, Allow it to be reassigned
# TODO: Share documents with specific people and allow them edit or just view (set permission)
# TODO: Show who edited the document and time
# TODO: csrf
# TODO: Add table to monitor document edits and statistics
# TODO: Endpoint to refresh token
# TODO: Endpoint to reset password
# TODO: Write tests



def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)

    if test_config is None:
        app.config.from_object(ApplicationConfig)
    else:
        app.config.from_mapping(test_config)

    app = Flask(__name__)
    print(app.config)
    CORS(app, supports_credentials=True, resources={r"/api/*": {"origins": [ApplicationConfig.FRONTEND]}})
    app.config.from_object(ApplicationConfig)
    jwt = JWTManager(app)

    db.init_app(app)
    migrate.init_app(app, db)

    with app.app_context():
        db.create_all()



    @jwt.unauthorized_loader
    def unauthorized_callback(callback):
        # No auth header
        print('not alooweddddd')
        response = make_response(jsonify({'error': "not authorized"}), 401)
        return response

    @jwt.invalid_token_loader
    def invalid_token_callback(jwt_header, jwt_payload):
        print('not valid')
        # Invalid Fresh/Non-Fresh Access token in auth header
        response = make_response(jsonify({'error': 'invalid credentials'}), 401)
        unset_access_cookies(response)
        return response

    # @jwt.expired_token_loader
    # @jwt_required()
    # def expired_token_callback(jwt_header, jwt_payload):
    #     print('needs refresh')
    #     # Expired auth header
    #     user_id = get_jwt_identity()
    #     access_token = create_access_token(identity=str(user_id))
    #     response = make_response(jsonify({'refresh': True}), 200)
    #     unset_access_cookies(response)
    #     set_access_cookies(response, access_token)

    #     return response
    
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        print('needs refresh')
        # Expired auth header
        response = make_response(redirect(url_for('refresh')))
        unset_access_cookies(response)
        return response, 302

    @app.get('/token/refresh')
    @jwt_required(refresh=True)
    def refresh():
        print('refresh token func')
        # Refreshing expired Access token
        user_id = get_jwt_identity()
        access_token = create_access_token(identity=str(user_id))
        response = make_response(jsonify({'refresh': True}), 200)
        set_access_cookies(response, access_token)
        return response
        


    # Routes
    @app.route('/api/v1/')
    @jwt_required()
    def welcome():
        return jsonify({ 'message': 'Welcome to Urrl' })


    @app.route("/api/v1/stats")
    def get_general_stats():
        url_pie = stats.url_pie
        document_pie = stats.document_pie
        stacked = stats.stacked
        line = stats.line

        return jsonify({
            'url_pie': url_pie,
            'document_pie': document_pie,
            'stacked': stacked,
            'line': line
        }), 200


    app.register_blueprint(auth)
    app.register_blueprint(user)
    app.register_blueprint(url)
    app.register_blueprint(document)

    return app