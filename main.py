from flask import Flask, redirect, url_for, render_template, request, Response, send_from_directory
from dotenv import load_dotenv
from constants import RICKROLL_LINK, UPLOAD_DIR
from jina import get_grass_touching_similarity

import os, flask_login, uuid, base64

if os.path.exists(".env"):
    load_dotenv(".env")

app = Flask(__name__)
app.secret_key = os.environ["FLASK_SECRET_KEY"]

login_manager = flask_login.LoginManager()
login_manager.init_app(app)

users = {}

class User(flask_login.UserMixin):
    pass

@login_manager.user_loader
def user_loader(user_id):
    return User.get(user_id)

@app.route("/iamarealpersonwhotouchedgrass")
@flask_login.login_required
def iamarealpersonwhotouchedgrass():
    return "You are a real person who touched grass! I can't believe this. You probably just tricked the AI or smth..."

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.jinja2")
    elif request.method == "POST":
        print(request.form)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.jinja2")
    elif request.method == "POST":
        username, password = request.form.get("username"), request.form.get("password")

        return "a"

@app.route("/upload", methods=["POST"])
def upload():
    try:
        image_type, image_data = request.json["image_type"], request.json["image_data"].encode("utf-8")

        image_data = image_data[23:] # data:image/jpeg;base64,

        image_uuid = uuid.uuid4()

        if image_type not in ["png", "jpeg"]:
            return "Invalid file type."

        if os.path.commonprefix((os.path.realpath(f"{UPLOAD_DIR}/{image_uuid}.{image_type}"), UPLOAD_DIR)) != UPLOAD_DIR:
            return "Why are you trying path traversal :C"

        with open(f"{UPLOAD_DIR}/{image_uuid}.{image_type}", "wb") as file:
            file.write(base64.b64decode(image_data))

    except:
        import traceback; traceback.print_exc()
        return Response("Unknown error", 400)

    grass_touching_similarity = get_grass_touching_similarity(url_for('uploads', filename=f"{image_uuid}.{image_type}"))
    if not grass_touching_similarity >= 0.8:
        return Response(f"Image not touching grass. Cosine similarity: {grass_touching_similarity}", 401)

    return Response(f"/uploads/{image_uuid}.{image_type}", 200)

@app.route("/uploads/<filename>")
def uploads(filename):
    return send_from_directory("uploads", filename)

@app.route("/info")
def info():
    return redirect(RICKROLL_LINK)

@app.route("/")
def main():
    if flask_login.current_user.is_authenticated:
        return redirect(url_for("iamarealpersonwhotouchedgrass"))
    else:
        return redirect(url_for("login"))

@app.route('/logout')
def logout():
    flask_login.logout_user()
    return 'Logged out'

@login_manager.unauthorized_handler
def unauthorized_handler():
    return redirect("/login")

app.run(debug=True)