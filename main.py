from flask import Flask, redirect, url_for, render_template, request, Response, send_from_directory, g
from dotenv import load_dotenv
from constants import RICKROLL_LINK, UPLOAD_DIR, MINIMUM_COSINE_SIMILARITY, DATABASE_FILE
from jina import get_grass_touching_similarity
from PIL import Image

import os, flask_login, uuid, base64, sqlite3, bcrypt, secrets, hashlib

if os.path.exists(".env"):
    load_dotenv(".env")

app = Flask(__name__)
app.secret_key = os.environ["FLASK_SECRET_KEY"]

login_manager = flask_login.LoginManager()
login_manager.init_app(app)

os.makedirs("uploads", exist_ok=True)

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE_FILE)
        db.execute("""
            CREATE TABLE IF NOT EXISTS Users (
                username TEXT PRIMARY KEY,
                password TEXT NOT NULL,
                password_salt TEXT NOT NULL
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS Images (
                username TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                image_hash TEXT NOT NULL
            )
        """)
        db.commit()
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

class User(flask_login.UserMixin):
    pass

@login_manager.user_loader
def user_loader(user_id):
    user = User()
    user.id = user_id
    return user

@app.route("/iamarealpersonwhotouchedgrass")
@flask_login.login_required
def iamarealpersonwhotouchedgrass():
    return "You are a real person who touched grass! I can't believe this. You probably just tricked the AI or smth..."

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.jinja2")
    elif request.method == "POST":
        username, password = request.form.get("username"), request.form.get("password")

        cur = get_db().cursor()

        cur.execute("SELECT password, password_salt FROM Users WHERE username = ?", (username,))

        row = cur.fetchone()
        if not row:
            cur.close()
            return Response("Unauthorized", 401)

        hashed_password, salt = row

        if secrets.compare_digest(bcrypt.hashpw(password.encode(), salt.encode()), hashed_password.encode()):
            cur.close()

            user = User()
            user.id = username
            flask_login.login_user(user, remember=True)

            return redirect(url_for("iamarealpersonwhotouchedgrass"))
        else:
            cur.close()
            return Response("Unathorized access. Just go outside, touch grass and make your own account...")
        
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.jinja2")
    elif request.method == "POST":
        username, password = request.form.get("username"), request.form.get("password")
        cur = get_db().cursor()

        cur.execute("SELECT username FROM Users WHERE username = ?", (username,))
        
        if cur.fetchone():
            return Response("An account with this username already exists", 400)

        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode(), salt)
        
        cur.execute("INSERT INTO Users (username, password, password_salt) VALUES (?, ?, ?)", (username, hashed_password.decode(), salt.decode()))
        get_db().commit()
        cur.close()

        user = User()
        user.id = username
        flask_login.login_user(user, remember=True)

        return redirect(url_for("iamarealpersonwhotouchedgrass"))

def resize_image_file(path, max_side=256, fmt="JPEG"):
    img = Image.open(path)
    scale = max_side / max(img.size)
    if scale < 1:
        img = img.resize((int(img.width * scale), int(img.height * scale)), Image.LANCZOS)
    img.save(path, format=fmt)

@app.route("/upload", methods=["POST"])
def upload():
    try:
        username, image_type, image_data = request.json["username"], request.json["image_type"], request.json["image_data"].encode("utf-8")

        if image_type == "jpeg":
            image_data = image_data[23:] # data:image/jpeg;base64,
        else:
            image_data = image_data[22:] # data:image/png;base64,

        image_uuid = uuid.uuid4()

        if image_type not in ["png", "jpeg"]:
            return Response("Invalid file type.", 400)

        if os.path.commonprefix((os.path.realpath(f"{UPLOAD_DIR}/{image_uuid}.{image_type}"), UPLOAD_DIR)) != UPLOAD_DIR:
            return Response("Why are you trying path traversal :C", 400)

        actual_image_data = base64.b64decode(image_data)
        image_hash = hashlib.sha512(actual_image_data).hexdigest()
        cur = get_db().cursor()
        cur.execute("SELECT image_hash FROM Images WHERE image_hash = ?", (image_hash,))
        if cur.fetchone():
            return Response("You can touch grass multiple times. I believe in you. Dont submit the same images.", 400)

        cur.execute("INSERT INTO Images (username, filename, image_hash) VALUES (?, ?, ?)", (username, image_uuid, image_hash))
        get_db().commit()

        with open(f"{UPLOAD_DIR}/{image_uuid}.{image_type}", "wb") as file:
            file.write(actual_image_data)

        resize_image_file(f"{UPLOAD_DIR}/{image_uuid}.{image_type}", fmt="JPEG" if image_type == "jpeg" else "png")

    except:
        import traceback; traceback.print_exc()
        return Response("Unknown error", 400)
    
    grass_touching_similarity = get_grass_touching_similarity(request.url_root.rstrip('/').replace("http://", "https://") + url_for('uploads', filename=f"{image_uuid}.{image_type}"))
    if not grass_touching_similarity >= MINIMUM_COSINE_SIMILARITY:
        return Response(f"Imagine not touching grass. Cosine similarity: {grass_touching_similarity}", 401)

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

app.run(port=os.environ.get("PORT"), host=os.environ.get("HOST", "0.0.0.0"))