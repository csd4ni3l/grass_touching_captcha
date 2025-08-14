from flask import Flask, redirect, url_for, render_template, request, Response, send_from_directory, g, flash
from dotenv import load_dotenv
from constants import RICKROLL_LINK, UPLOAD_DIR, MINIMUM_COSINE_SIMILARITY, MINIMUM_OCR_SIMILARITY, DATABASE_FILE
from PIL import Image

from jina import get_grass_touching_similarity
from ocr_check import generate_challenge, check_text_similarity

import os, flask_login, uuid, base64, sqlite3, bcrypt, secrets, hashlib, time, threading

if os.path.exists(".env"):
    load_dotenv(".env")

app = Flask(__name__)
app.secret_key = os.environ["FLASK_SECRET_KEY"]

login_manager = flask_login.LoginManager()
login_manager.init_app(app)

global challenges
challenges = {}

os.makedirs("uploads", exist_ok=True)

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE_FILE)
        db.execute("""
            CREATE TABLE IF NOT EXISTS Users (
                username TEXT PRIMARY KEY,
                last_grass_touch_time TEXT NOT NULL,
                grass_touching_count INT NOT NULL,
                banned BOOL NOT NULL,
                password TEXT NOT NULL,
                password_salt TEXT NOT NULL
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS Images (
                image_hash TEXT PRIMARY KEY,
                username TEXT NOT NULL,
                filename TEXT NOT NULL
            )
        """)
        db.commit()
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def check_grass_touching_bans():
    while True:
        with app.app_context():
            cur = get_db().cursor()
            
            cur.execute("SELECT username, last_grass_touch_time FROM Users")
            for user in cur.fetchall():
                if time.time() - float(user[1]) >= (24 * 3600):
                    cur.execute("UPDATE users SET banned = ? WHERE username = ?", (True, user[0]))
            
            get_db().commit()
            cur.close()

            time.sleep(60)

threading.Thread(target=check_grass_touching_bans, daemon=True).start()

class User(flask_login.UserMixin):
    pass

@login_manager.user_loader
def user_loader(user_id):
    user = User()
    user.id = user_id
    return user

@login_manager.unauthorized_handler
def unauthorized_handler():
    return redirect(url_for("login"))

@app.before_request
def check_banned():
    username = flask_login.current_user.id
    
    cur = get_db().cursor()
    cur.execute("SELECT banned FROM Users WHERE username = ?", (username))
    row = cur.fetchone()
    cur.close()

    if row is None or row[0]:
        flash("Imagine forgetting to touch grass so you get banned from my app. Such a discord moderator you are. You have no life. Just go outside.")
        flask_login.logout_user()
        return redirect("/")

def resize_image_file(path, max_side=256, fmt="JPEG"):
    img = Image.open(path)
    scale = max_side / max(img.size)
    if scale < 1:
        img = img.resize((int(img.width * scale), int(img.height * scale)), Image.LANCZOS)
    img.save(path, format=fmt)

@app.route("/grass_touch_submit", methods=["POST"])
@flask_login.login_required
def submit_grass_touching():
    username = flask_login.current_user.id

    if not challenges.get(username):
        return Response("Start and finish a challenge before submitting the grass touching.", 401)
    
    if not challenges[username]["completed"]:
        return Response("Finish a challenge before submitting the grass touching.", 401)

    cur = get_db().cursor()

    cur.execute("UPDATE Users SET grass_touching_count = grass_touching_count + 1 WHERE username = ?", (username,))
    cur.execute("UPDATE Users SET last_grass_touch_time = ? WHERE username = ?", (time.time(), username))

    get_db().commit()

    cur.close()

    return redirect("/")

@app.route("/submit_grasstouching")
@flask_login.login_required
def submit_grasstouching():
    username = flask_login.current_user.id
    return render_template("submit_grass_touching.jinja2", username=username)

@app.route("/generate_challenge", methods=["POST"])
def generate_challenge_route():
    username = request.json["username"]

    if not username in challenges:
        challenges[username] = {"text": generate_challenge(username), "completed": False}

    return challenges[username]["text"]

@app.route("/submit_challenge", methods=["POST"])
def submit_challenge():
    try:
        username, image_type, image_data = request.json["username"], request.json["image_type"], request.json["image_data"].encode("utf-8")

        if image_type == "jpeg":
            image_data = image_data[23:] # data:image/jpeg;base64,
        else:
            image_data = image_data[22:] # data:image/png;base64,

        image_uuid = str(uuid.uuid4())

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

        cur.execute("INSERT INTO Images (image_hash, username, filename) VALUES (?, ?, ?)", (image_hash, username, image_uuid))
        get_db().commit()

        with open(f"{UPLOAD_DIR}/{image_uuid}.{image_type}", "wb") as file:
            file.write(actual_image_data)

        resize_image_file(f"{UPLOAD_DIR}/{image_uuid}.{image_type}", fmt="JPEG" if image_type == "jpeg" else "png")

    except:
        import traceback; traceback.print_exc()
        return Response("Unknown error", 400)
    
    if not challenges.get(username):
        return Response("You havent started a challenge yet.", 400)
    
    detected_text, text_similarity = check_text_similarity(f"{UPLOAD_DIR}/{image_uuid}.{image_type}", challenges[username]["text"])

    if not text_similarity >= MINIMUM_OCR_SIMILARITY:
        return Response(f"The text is incorrect on the image. Similarity: {round(text_similarity * 100, 2)}% Detected Text: {detected_text}", 400)
    
    grass_touching_similarity = get_grass_touching_similarity(request.url_root.rstrip('/').replace("http://", "https://") + url_for('uploads', filename=f"{image_uuid}.{image_type}"))
    if not grass_touching_similarity >= MINIMUM_COSINE_SIMILARITY:
        os.remove(f"{UPLOAD_DIR}/{image_uuid}.{image_type}")
        return Response(f"Imagine not touching grass. Cosine similarity: {grass_touching_similarity}", 401)

    challenges[username]['completed'] = True

    return Response(f"/uploads/{image_uuid}.{image_type}", 200)

@app.route("/")
def application():
    username = flask_login.current_user.id if hasattr(flask_login.current_user, "id") else ""

    return render_template("home.jinja2", username=username)

@app.route("/leaderboard")
def leaderboard():
    username = flask_login.current_user.id if hasattr(flask_login.current_user, "id") else ""

    cur = get_db().cursor()

    cur.execute("SELECT grass_touching_count, banned, username FROM USERS ORDER BY grass_touching_count DESC, username ASC LIMIT 25")

    users = cur.fetchall()
    if not users:
        cur.close()
        return Response("DB is not healthy.", 401)

    cur.close()

    return render_template("leaderboard.jinja2", users=users, current_username=username)

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

            return redirect(url_for("application"))
        else:
            cur.close()
            return Response("Unathorized access. Just go outside, touch grass and make your own account...", 401)
        
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.jinja2")
    elif request.method == "POST":
        username, password = request.form.get("username"), request.form.get("password")
        
        if not challenges.get(username):
            return Response("Start and finish a challenge before registering.", 401)
        
        if not challenges[username]["completed"]:
            return Response("Finish a challenge before registering.", 401)

        challenges.pop(username)

        cur = get_db().cursor()

        cur.execute("SELECT username FROM Users WHERE username = ?", (username,))
        
        if cur.fetchone():
            return Response("An account with this username already exists", 400)

        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode(), salt)
        
        cur.execute("INSERT INTO Users (username, password, password_salt, last_grass_touch_time, grass_touching_count, banned) VALUES (?, ?, ?, ?, ?, ?)", (username, hashed_password.decode(), salt.decode(), time.time(), 1, False))
        get_db().commit()
        cur.close()

        return redirect(url_for("login"))
    
@app.route("/uploads/<filename>")
def uploads(filename):
    return send_from_directory("uploads", filename)

@app.route("/info")
def info():
    return redirect(RICKROLL_LINK)

@app.route('/logout')
def logout():
    flask_login.logout_user()
    return redirect("/")

app.run(port=os.environ.get("PORT"), host=os.environ.get("HOST", "0.0.0.0"))