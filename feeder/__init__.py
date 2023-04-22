import os

import strawberry
from flask import Flask
from flask_cors import CORS
from strawberry.flask.views import AsyncGraphQLView
from werkzeug.security import generate_password_hash

from .models import User


def create_app(db_uri="sqlite+pysqlite:///test.db"):
    app = Flask(__name__)

    CORS(app, resources={r"/graphql": {"origins": "*"}})

    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "SQLALCHEMY_DATABASE_URI", db_uri
    )

    if app.debug:
        app.config["SQLALCHEMY_RECORD_QUERIES"] = True
        app.config["DEBUG_TB_INTERCEPT_REDIRECTS"] = False
        app.config["SQLALCHEMY_ECHO"] = True

    from .db import db
    from .schema import Mutation, Query

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    app.add_url_rule(
        "/graphql",
        view_func=AsyncGraphQLView.as_view("graphql_view", schema=schema),
    )

    db.init_app(app)

    with app.app_context():
        db.create_all()
        if not db.session.get(User, 1):
            db.session.add(
                User(
                    email="jack@evans.gb.net", password=generate_password_hash("admin")
                )
            )
            db.session.commit()

    return app
