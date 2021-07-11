from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import datetime
import flask_praetorian
from flask_cors import CORS, cross_origin

app = Flask(__name__)

app.config["SECRET_KEY"] = "hjajha6886bnajaasdg"
app.config[
    "SQLALCHEMY_DATABASE_URI"
] = "mysql+pymysql://root:root@localhost:8889/new_knomi"
app.config["CORS_HEADERS"] = "Content-Type"
app.config["JWT_ACCESS_LIFESPAN"] = {"minutes": 1}
app.config["JWT_REFRESH_LIFESPAN"] = {"minutes": 30}

db = SQLAlchemy(app)
guard = flask_praetorian.Praetorian()
migrate = Migrate(app, db)
cors = CORS(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50))
    password = db.Column(db.String(300))
    roles = db.Column(db.String(80))
    is_active = db.Column(db.Boolean)

    @property
    def identity(self):

        return self.id

    @property
    def rolenames(self):

        try:
            return self.roles.split(",")
        except Exception:
            return []

    @classmethod
    def lookup(cls, username):

        return cls.query.filter_by(username=username).one_or_none()

    @classmethod
    def identify(cls, id):

        return cls.query.get(id)

    def is_valid(self):
        return self.is_active


guard.init_app(app, User)


@app.route("/")
def index():
    return "hello"


########### USER ACCOUNT ##########


@app.route("/user", methods=["POST"])
def create_user():

    data = request.get_json()

    my_password = guard.hash_password(data["password"])

    new_user = User(
        username=data["username"],
        password=my_password,
        roles=data["roles"],
        is_active=True,
    )

    db.session.add(new_user)
    db.session.commit()

    username_message = data["username"]

    return {"message": "{} created!".format(username_message)}


@app.route("/login", methods=["POST"])
@cross_origin()
def login():

    data = request.get_json()
    username = data["username"]
    password = data["password"]
    user = guard.authenticate(username, password)
    token = {"token": guard.encode_jwt_token(user)}
    return token, 200


@app.route("/login/refresh", methods=["POST"])
def refresh():

    data = request.get_json()
    new_token = guard.refresh_jwt_token(data["token"])
    token = {"token": new_token}
    return token, 200


@app.route("/protected")
@flask_praetorian.auth_required
def protected():

    return {
        "message": "protected endpoint (allowed user {})".format(
            flask_praetorian.current_user().username
        )
    }


@app.route("/protected_admin_required")
@flask_praetorian.roles_required("admin")
def protected_admin_required():

    return {
        "message": "protected_admin_required endpoint (allowed user {})".format(
            flask_praetorian.current_user().username,
        )
    }


@app.route("/protected_user_accepted")
@flask_praetorian.roles_accepted("user", "admin")
def protected_user_accepted():

    return {
        "message": "protected_user_accepted endpoint (allowed user {})".format(
            flask_praetorian.current_user().username,
        )
    }


if __name__ == "__main__":
    app.run(debug=True)
