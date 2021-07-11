from flask import Flask, request, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy.orm.query import Query
from werkzeug.security import check_password_hash, generate_password_hash
import uuid
import jwt
import datetime
from functools import wraps
from flask_cors import CORS, cross_origin

app = Flask(__name__)

app.config["SECRET_KEY"] = "hjajha6886bnajaasdg"
app.config[
    "SQLALCHEMY_DATABASE_URI"
] = "mysql+pymysql://root:root@localhost:8889/new_knomi"
app.config["CORS_HEADERS"] = "Content-Type"

db = SQLAlchemy(app)
migrate = Migrate(app, db)
cors = CORS(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(50), unique=True)
    username = db.Column(db.String(50))
    password = db.Column(db.String(80))
    admin = db.Column(db.Boolean)


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(300))


class SubCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subcategory = db.Column(db.String(300))
    id_category = db.Column(db.Integer)


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    answer = db.Column(db.Text)
    id_category = db.Column(db.Integer, db.ForeignKey("category.id"))
    id_subcategory = db.Column(db.Integer, db.ForeignKey("sub_category.id"))
    create_date = db.Column(db.DateTime)
    public_id_creator = db.Column(db.String(50))
    # one post to many keywords relationship
    keywords = db.relationship("Keyword", backref="post", lazy="dynamic")


class Keyword(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    keyword = db.Column(db.String(300))
    id_post = db.Column(db.Integer, db.ForeignKey("post.id"))


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if "x-access-token" in request.headers:
            token = request.headers["x-access-token"]

        if not token:
            return {"message": "Token is missing!"}, 401

        try:
            data = jwt.decode(token, app.config["SECRET_KEY"])
            current_user = User.query.filter_by(public_id=data["public_id"]).first()
        except:
            return {"message": "Token is invalid!"}, 401

        return f(current_user, *args, **kwargs)

    return decorated


@app.route("/")
def index():
    return "hello"


########### USER ACCOUNT ##########


@app.route("/user", methods=["POST"])
@token_required
def create_user(current_user):

    if not current_user.admin:
        return {"message": "Cannot perform that function!"}

    data = request.get_json()
    # test
    # print(type(data))
    # <class 'dict'>
    # print(data)
    # {'username': 'admin', 'password': 'admin'}

    hashed_password = generate_password_hash(data["password"], method="sha256")

    new_user = User(
        public_id=str(uuid.uuid4()),
        username=data["username"],
        password=hashed_password,
        admin=False,
    )

    db.session.add(new_user)
    db.session.commit()

    username_message = data["username"]

    return {"message": "{} created!".format(username_message)}


@app.route("/user", methods=["GET"])
@token_required
def get_all_users(current_user):

    if not current_user.admin:
        return {"message": "Cannot perform that function!"}

    users = User.query.all()
    # print(users)
    # >> [<User 1>, <User 2>, <User 3>]

    output = []

    for user in users:
        # print(type(user))
        # >> <class '__main__.User'>
        # print(user)
        # <User 1>
        # this is object so take the value and create new dictionary for python then return as json. Python dictionary and json has same format {"name":"adithya"} BUT object is different, format is {name:"adithya"}.

        user_data = {}
        user_data["public_id"] = user.public_id
        user_data["username"] = user.username
        user_data["password"] = user.password
        user_data["admin"] = user.admin
        output.append(user_data)

    return {"users": output}


@app.route("/user/<public_id>", methods=["GET"])
@token_required
def get_one_user(current_user, public_id):

    if not current_user.admin:
        return {"message": "Cannot perform that function!"}

    user = User.query.filter_by(public_id=public_id).first()

    if not user:
        return {"message": "No user found!"}

    user_data = {}
    user_data["public_id"] = user.public_id
    user_data["username"] = user.username
    user_data["password"] = user.password
    user_data["admin"] = user.admin

    return {"user": user_data}


# @app.route("/user/<public_id>", methods=["PUT"])
# @token_required
# def change_user_status(current_user, public_id):

#     if not current_user.admin:
#         return {"message": "Cannot perform that function!"}

#     user = User.query.filter_by(public_id=public_id).first()

#     if not user:
#         return {"message": "No user found!"}

#     data = request.get_json()

#     if data["username"]:

#         user.username = data["username"]

#         db.session.commit()

#         username_message = True
#     else:
#         username_message = False

#     if data["password"]:
#         hashed_password = generate_password_hash(data["password"], method="sha256")

#         user.password = hashed_password

#         db.session.commit()

#         password_message = True
#     else:
#         password_message = False

#     if data["admin"] is not None:
#         user.admin = data["admin"]

#         db.session.commit()

#         status_message = "promote to admin"
#     else:
#         status_message = "change to user"

#     return {
#         "username_message": username_message,
#         "password_message": password_message,
#         "status_message": status_message,
#     }


@app.route("/user/<public_id>", methods=["PUT"])
@token_required
def update_user_account(current_user, public_id):

    if not current_user.admin:
        return {"message": "Cannot perform that function!"}

    user = User.query.filter_by(public_id=public_id).first()

    if not user:
        return {"message": "No user found!"}

    data = request.get_json()

    if data["username"]:
        user.username = data["username"]
        db.session.commit()

    if data["password"]:
        hashed_password = generate_password_hash(data["password"], method="sha256")
        user.password = hashed_password
        db.session.commit()

    if data["admin"] is not None:
        user.admin = data["admin"]
        db.session.commit()

    return {"message": "user status has been updated"}


@app.route("/user", methods=["DELETE"])
@token_required
def delete_selected_user(current_user):

    if not current_user.admin:
        return {"message": "Cannot perform that function!"}

    # format in postman must be JSON unless will get None Type
    data = request.get_json()
    # expect >> data = {{"selected_users": ["7387b03d-4649-4be7-83fa-77c5a58bf0f2", "32958342-4fad-4a98-b4f4-becb3befb519", "8ae6d299-88cd-476e-8602-ac4480c87dec"]}}

    list_deleted = []

    for i in data["selected_user"]:
        delete_selected = User.query.filter_by(public_id=i).first()

        username = delete_selected.username

        db.session.delete(delete_selected)
        db.session.commit()

        list_deleted.append(username)

    # convert list to str for message, merge list then separate it with ", "
    # The join() method returns a string created by joining the elements of an iterable by string separator
    # If the iterable contains any non-string values, it raises a TypeError exception.

    separator = ", "
    list_to_string = separator.join(list_deleted)

    return {"message": "{} has been deleted".format(list_to_string)}


@app.route("/user/<public_id>", methods=["DELETE"])
@token_required
def delete_one_user(current_user, public_id):

    if not current_user.admin:
        return {"message": "Cannot perform that function!"}

    user = User.query.filter_by(public_id=public_id).first()

    if not user:
        return {"message": "No user found!"}

    user_deleted = user.username

    db.session.delete(user)
    db.session.commit()

    return {"message": "{} has been deleted".format(user_deleted)}


########### LOGIN ###########
@app.route("/login")
@cross_origin()
def login():
    # test = request
    # print(test)
    auth = request.authorization
    # print(auth)

    if not auth or not auth.username or not auth.password:
        return make_response(
            "Could not verify",
            401,
            {"WWW-Authenticate": "Basic realm='Login required!'"},
        )

    user = User.query.filter_by(username=auth.username).first()

    if not user:
        return make_response(
            "Could not verify",
            401,
            {"WWW-Authenticate": "Basic realm='Login required!'"},
        )

    if check_password_hash(user.password, auth.password):
        token = jwt.encode(
            {
                "public_id": user.public_id,
                "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=30),
            },
            app.config["SECRET_KEY"],
        )

        return {"token": token.decode("UTF-8")}

    return make_response(
        "Could not verify", 401, {"WWW-Authenticate": "Basic realm='Login required!'"}
    )


############ DEPENDENCY DROPDOWN ###########

# >>>> CATEGORY <<<<<


@app.route("/category", methods=["POST"])
@token_required
def create_category(current_user):

    if not current_user.admin:
        return {"message": "Cannot perform that function!"}

    data = request.get_json()

    new_category = Category(category=data["category"])

    db.session.add(new_category)
    db.session.commit()

    category_message = data["category"]

    return {"message": "{} created!".format(category_message)}


@app.route("/category", methods=["GET"])
@token_required
def get_all_categories(current_user):

    if not current_user.admin:
        return {"message": "Cannot perform that function!"}

    categories = Category.query.all()

    output = []

    for category in categories:

        category_data = {}
        category_data["id"] = category.id
        category_data["category"] = category.category

        output.append(category_data)

    return {"categories": output}


@app.route("/category/<id>", methods=["GET"])
@token_required
def get_one_category(current_user, id):

    if not current_user.admin:
        return {"message": "Cannot perform that function!"}

    category = Category.query.filter_by(id=id).first()

    if not category:
        return {"message": "No user found!"}

    category_data = {}
    category_data["id"] = category.id
    category_data["category"] = category.category

    return {"user": category_data}


@app.route("/category/<id>", methods=["PUT"])
@token_required
def update_category(current_user, id):

    if not current_user.admin:
        return {"message": "Cannot perform that function!"}

    category = Category.query.filter_by(id=id).first()

    if not category:
        return {"message": "No category found!"}

    data = request.get_json()

    if data["category"]:
        category.category = data["category"]
        db.session.commit()

    return {"message": "category has been updated to {}!".format(category.category)}


@app.route("/category", methods=["DELETE"])
@token_required
def delete_selected_category(current_user):

    if not current_user.admin:
        return {"message": "Cannot perform that function!"}

    data = request.get_json()

    list_deleted = []

    for i in data["selected_category"]:
        delete_selected = Category.query.filter_by(id=i).first()

        category = delete_selected.category

        db.session.delete(delete_selected)
        db.session.commit()

        list_deleted.append(category)

    separator = ", "
    list_to_string = separator.join(list_deleted)

    return {"message": "{} has been deleted".format(list_to_string)}


@app.route("/category/<id>", methods=["DELETE"])
@token_required
def delete_one_category(current_user, id):

    if not current_user.admin:
        return {"message": "Cannot perform that function!"}

    category = Category.query.filter_by(id=id).first()

    if not category:
        return {"message": "No category found!"}

    category_deleted = category.category

    db.session.delete(category)
    db.session.commit()

    return {"message": "{} has been deleted".format(category_deleted)}


# >>>> SUBCATEGORY <<<<<


@app.route("/subcategory", methods=["POST"])
@token_required
def create_subcategory(current_user):

    if not current_user.admin:
        return {"message": "Cannot perform that function!"}

    data = request.get_json()

    new_subcategory = SubCategory(
        subcategory=data["subcategory"], id_category=data["id_category"]
    )

    db.session.add(new_subcategory)
    db.session.commit()

    data_category = Category.query.filter_by(id=data["id_category"]).first()

    subcategory_message = data["subcategory"]
    category_message = data_category.category

    return {
        "message": "{} from {} created!".format(subcategory_message, category_message)
    }


@app.route("/subcategory", methods=["GET"])
@token_required
def get_all_subcategories(current_user):

    if not current_user.admin:
        return {"message": "Cannot perform that function!"}

    subcategories = SubCategory.query.all()

    output = []

    for subcategory in subcategories:

        subcategory_data = {}
        subcategory_data["id"] = subcategory.id
        subcategory_data["subcategory"] = subcategory.subcategory
        subcategory_data["id_category"] = subcategory.id_category

        output.append(subcategory_data)

    return {"subcategories": output}


@app.route("/subcategory/<id_category>", methods=["GET"])
@token_required
def get_one_subcategory(current_user, id_category):

    if not current_user.admin:
        return {"message": "Cannot perform that function!"}

    subcategories = SubCategory.query.filter_by(id_category=id_category).all()

    if not subcategories:
        return {"message": "No user found!"}

    output = []

    for subcategory in subcategories:
        subcategory_data = {}
        subcategory_data["id"] = subcategory.id
        subcategory_data["subcategory"] = subcategory.subcategory
        output.append(subcategory_data)

    return {"subcategory": output}


@app.route("/subcategory/<id>", methods=["PUT"])
@token_required
def update_subcategory(current_user, id):

    if not current_user.admin:
        return {"message": "Cannot perform that function!"}

    subcategory = SubCategory.query.filter_by(id=id).first()

    if not subcategory:
        return {"message": "No subcategory found!"}

    data = request.get_json()

    if data["subcategory"]:
        subcategory.subcategory = data["subcategory"]
        subcategory.id_category = data["id_category"]
        db.session.commit()

    return {"message": "subcategory has been updated!"}


@app.route("/subcategory", methods=["DELETE"])
@token_required
def delete_selected_subcategory(current_user):

    if not current_user.admin:
        return {"message": "Cannot perform that function!"}

    data = request.get_json()

    list_deleted = []

    for i in data["selected_subcategory"]:
        delete_selected = SubCategory.query.filter_by(id=i).first()

        subcategory = delete_selected.subcategory

        db.session.delete(delete_selected)
        db.session.commit()

        list_deleted.append(subcategory)

    separator = ", "
    list_to_string = separator.join(list_deleted)

    return {"message": "{} has been deleted".format(list_to_string)}


@app.route("/subcategory/<id>", methods=["DELETE"])
@token_required
def delete_one_subcategory(current_user, id):

    if not current_user.admin:
        return {"message": "Cannot perform that function!"}

    subcategory = SubCategory.query.filter_by(id=id).first()

    if not subcategory:
        return {"message": "No subcategory found!"}

    subcategory_deleted = subcategory.subcategory

    db.session.delete(subcategory)
    db.session.commit()

    return {"message": "{} has been deleted".format(subcategory_deleted)}


############ POST ###########
@app.route("/post", methods=["POST"])
@token_required
def create_post(current_user):

    # if not current_user.admin:
    #     return {"message": "Cannot perform that function!"}

    data = request.get_json()

    new_post = Post(
        answer=data["answer"],
        id_category=data["id_category"],
        id_subcategory=data["id_subcategory"],
        create_date=datetime.datetime.utcnow(),
        public_id_creator=current_user.public_id,
    )

    db.session.add(new_post)
    db.session.commit()

    for i in data["keywords"]:
        # post is from backref='post' so it can automatically add id to id_post in Keyword table
        # new_post from new added data. new_post = Post(answer=..)
        # not only for new added but you can use backref with query, ex : new_post = Post.query.filter_by(answer=..).first()
        new_keyword = Keyword(keyword=i, post=new_post)
        db.session.add(new_keyword)
        db.session.commit()

        # we can alson accsess it.
        # ex : new_post = Post.query.filter_by(answer=..).first()
        # new_post.answer >> '...' ;
        # new_post.posts >> [<Keyword 1>,<Kyword 2>]
        # new_post.posts[0] >> <Keyword>
        # new_post.posts[0].keyword >> 'mangga'

    return {"message": "new post created!"}


@app.route("/post", methods=["GET"])
@token_required
# must passing current_user as parameter function
def get_all_posts(current_user):

    posts = Post.query.all()

    output = []

    for post in posts:

        post_data = {}
        post_data["id"] = post.id
        post_data["answer"] = post.answer
        post_data["id_category"] = post.id_category
        post_data["id_subcategory"] = post.id_subcategory

        keywords = Keyword.query.filter_by(id_post=post.id).all()

        keyword_list = []

        for keyword in keywords:
            keyword_list.append(keyword.keyword)

        post_data["keywords"] = keyword_list

        output.append(post_data)

    return {"posts": output}


@app.route("/post/<id>", methods=["GET"])
@token_required
def get_post(current_user, id):

    post = Post.query.filter_by(id=id).first()

    if not post:
        return {"message": "No post found!"}

    post_data = {}
    post_data["id"] = post.id
    post_data["answer"] = post.answer
    post_data["id_category"] = post.id_category
    post_data["id_subcategory"] = post.id_subcategory

    keywords = Keyword.query.filter_by(id_post=id)

    keyword_list = []

    for keyword in keywords:
        keyword_list.append(keyword.keyword)

    # if wanna return list of object use this, if only wanna return list use bellow instead
    # for keyword in keywords:
    #     keyword_data = {}
    #     keyword_data["id"] = keyword.id
    #     keyword_data["keyword"] = keyword.keyword
    #     keyword_output.append(keyword_data)

    post_data["keyword"] = keyword_list

    return {"post": post_data}


@app.route("/post/<id>", methods=["PUT"])
@token_required
def update_post(current_user, id):

    post = Post.query.filter_by(id=id).first()

    if not post:
        return {"message": "No post found!"}

    data = request.get_json()

    post.answer = data["answer"]
    post.id_category = data["id_category"]
    post.id_subcategory = data["id_subcategory"]

    db.session.commit()

    for i in data["keywords"]:
        new_keyword = Keyword.query.filter_by(keyword=i).first()

        if not new_keyword:
            new_keyword = Keyword(keyword=i, post=post)
            db.session.add(new_keyword)
            db.session.commit()

    return {"message": "post has been updated!"}


@app.route("/post/keyword/<id>", methods=["DELETE"])
@token_required
def delete_one_keyword(current_user, id):

    keyword = Keyword.query.filter_by(id=id).first()

    if not keyword:
        return {"message": "No keyword found!"}

    keyword_deleted = keyword.keyword

    db.session.delete(keyword)
    db.session.commit()

    return {"message": "{} has been deleted".format(keyword_deleted)}


@app.route("/post/<id>", methods=["DELETE"])
@token_required
def delete_one_post(current_user, id):

    post = Post.query.filter_by(id=id).first()

    if not post:
        return {"message": "No post found!"}

    keywords = Keyword.query.filter_by(id_post=id).all()

    for keyword in keywords:
        db.session.delete(keyword)
        db.session.commit()

    db.session.delete(post)
    db.session.commit()

    return {"message": "post has been deleted"}


@app.route("/post", methods=["DELETE"])
@token_required
def delete_selected_post(current_user):

    data = request.get_json()

    for i in data["selected_post"]:

        keywords = Keyword.query.filter_by(id_post=i).all()
        for keyword in keywords:
            db.session.delete(keyword)
            db.session.commit()

        delete_selected = Post.query.filter_by(id=i).first()

        db.session.delete(delete_selected)
        db.session.commit()

    return {"message": "selected post has been deleted"}


if __name__ == "__main__":
    app.run(debug=True)
