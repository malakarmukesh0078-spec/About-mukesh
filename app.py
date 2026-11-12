import os, json, uuid, secrets, time
from functools import wraps
from flask import (Flask, render_template, request, redirect, url_for,
                   session, send_from_directory, abort, flash)
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

BASE = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE, "data.json")
UPLOADS = os.path.join(BASE, "uploads")
SECRET_FILE = os.path.join(BASE, ".secret_key")
os.makedirs(UPLOADS, exist_ok=True)

# Default admin password (change it from the admin panel after first login)
DEFAULT_PASSWORD = os.environ.get("ADMIN_PASSWORD", "mukesh@123")
ADMIN_PATH = "/mukesh"

ALLOWED = {"png", "jpg", "jpeg", "gif", "webp", "svg", "mp4", "webm", "mov"}
IMG_EXT = {"png", "jpg", "jpeg", "gif", "webp", "svg"}

DEFAULTS = {
    "settings": {
        "site_title": "Mukesh Malakar",
        "first_name": "Mukesh",
        "last_name": "Malakar",
        "tagline": "Entrepreneur and creator from Raigarh, Chhattisgarh. I build, create and serve with a local heart.",
        "roles": "Entrepreneur, Creator, Storyteller, Raigarh Ka Beta",
        "about_title": "About me",
        "about": "Namaste! I'm Mukesh Malakar, born and raised in Raigarh, Chhattisgarh. "
                 "This is the place where I share my work, my stories and what I'm building. "
                 "Edit this paragraph from the admin panel.",
        "logo": "",
        "banner": "",
        "photo": "",
        "banner_text": "Welcome to my world",
        "color_primary": "#f5b83d",
        "color_accent": "#34c3b0",
        "color_bg": "#0e1424",
        "skills_title": "What I can do",
        "skills": "fa-solid fa-camera|Photography|Product shoots, portraits and photo editing\n"
                  "fa-solid fa-video|Video & Reels|Shooting, editing and short-form content\n"
                  "fa-solid fa-laptop-code|Web & Social|Websites, pages and online presence\n"
                  "fa-solid fa-handshake|Business|Retail, sales and customer service",
        "stats": "50+|Projects\n3+|Years of experience\n100+|Happy customers",
        "cta_text": "Have a project or an idea? Let's talk.",
        "phone": "+91 00000 00000",
        "whatsapp": "910000000000",
        "email": "yourmail@example.com",
        "instagram": "https://instagram.com/",
        "facebook": "",
        "youtube": "",
        "address": "Raigarh, Chhattisgarh, India",
        "map_title": "Raigarh, Chhattisgarh",
        "footer": "© 2026 Mukesh Malakar. All rights reserved.",
    },
    "items": [],
    "password_hash": "",
}


def load():
    if not os.path.exists(DATA_FILE):
        save(DEFAULTS)
        return json.loads(json.dumps(DEFAULTS))
    with open(DATA_FILE, encoding="utf-8") as f:
        d = json.load(f)
    for k, v in DEFAULTS["settings"].items():
        d["settings"].setdefault(k, v)
    d.setdefault("items", [])
    d.setdefault("password_hash", "")
    return d


def save(d):
    tmp = DATA_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    os.replace(tmp, DATA_FILE)


def secret():
    if os.environ.get("SECRET_KEY"):
        return os.environ["SECRET_KEY"]
    if not os.path.exists(SECRET_FILE):
        with open(SECRET_FILE, "w") as f:
            f.write(secrets.token_hex(32))
    return open(SECRET_FILE).read().strip()


app = Flask(__name__)
app.secret_key = secret()
app.config["MAX_CONTENT_LENGTH"] = 200 * 1024 * 1024
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"


def parse_lines(text, n):
    out = []
    for line in (text or "").splitlines():
        parts = [p.strip() for p in line.split("|")]
        if len(parts) >= 2 and parts[0]:
            parts += [""] * (n - len(parts))
            out.append(parts[:n])
    return out


def yt_embed(url):
    if not url:
        return ""
    if "youtu.be/" in url:
        vid = url.split("youtu.be/")[1].split("?")[0]
        return "https://www.youtube.com/embed/" + vid
    if "youtube.com/watch" in url and "v=" in url:
        vid = url.split("v=")[1].split("&")[0]
        return "https://www.youtube.com/embed/" + vid
    return ""


@app.context_processor
def inject():
    d = load()
    s = d["settings"]
    return dict(s=s, skills=parse_lines(s["skills"], 3),
                stats=parse_lines(s["stats"], 2),
                roles=[r.strip() for r in s["roles"].split(",") if r.strip()],
                yt_embed=yt_embed, csrf=csrf_token, admin_path=ADMIN_PATH)


def csrf_token():
    if "csrf" not in session:
        session["csrf"] = secrets.token_hex(16)
    return session["csrf"]


def check_csrf():
    if request.form.get("csrf") != session.get("csrf"):
        abort(400)


def admin_required(f):
    @wraps(f)
    def w(*a, **k):
        if not session.get("admin"):
            return redirect(url_for("admin"))
        return f(*a, **k)
    return w


def save_upload(field, allowed=ALLOWED):
    f = request.files.get(field)
    if not f or not f.filename:
        return None
    ext = f.filename.rsplit(".", 1)[-1].lower() if "." in f.filename else ""
    if ext not in allowed:
        flash("File type not allowed: ." + ext)
        return None
    name = uuid.uuid4().hex[:12] + "_" + secure_filename(f.filename)
    f.save(os.path.join(UPLOADS, name))
    return name


def remove_file(name):
    if name:
        p = os.path.join(UPLOADS, os.path.basename(name))
        if os.path.exists(p):
            os.remove(p)


# ---------------- Public pages ----------------
@app.route("/")
def home():
    d = load()
    return render_template("home.html", page="home", featured=d["items"][::-1][:3])


@app.route("/portfolio")
def portfolio():
    d = load()
    items = d["items"][::-1]
    cats = sorted({i.get("category", "") for i in items if i.get("category")})
    return render_template("portfolio.html", page="portfolio", items=items, cats=cats,
                           IMG_EXT=IMG_EXT)


@app.route("/contact")
def contact():
    return render_template("contact.html", page="contact")


@app.route("/uploads/<path:name>")
def uploads(name):
    return send_from_directory(UPLOADS, name)


# ---------------- Admin ----------------
@app.route(ADMIN_PATH, methods=["GET", "POST"])
def admin():
    d = load()
    if request.method == "POST" and not session.get("admin"):
        check_csrf()
        time.sleep(0.8)  # brute-force slow
        pw = request.form.get("password", "")
        ok = (check_password_hash(d["password_hash"], pw) if d["password_hash"]
              else secrets.compare_digest(pw, DEFAULT_PASSWORD))
        if ok:
            session["admin"] = True
            return redirect(url_for("admin"))
        flash("Wrong password.")
        return redirect(url_for("admin"))
    if not session.get("admin"):
        return render_template("login.html", page="login")
    return render_template("admin.html", page="admin", items=d["items"])


@app.route(ADMIN_PATH + "/logout")
def logout():
    session.pop("admin", None)
    return redirect(url_for("home"))


TEXT_FIELDS = ["site_title", "first_name", "last_name", "tagline", "roles", "about_title",
               "about", "cta_text", "banner_text", "color_primary", "color_accent", "color_bg",
               "skills_title", "skills", "stats", "phone", "whatsapp", "email",
               "instagram", "facebook", "youtube", "address", "map_title", "footer"]


@app.route(ADMIN_PATH + "/settings", methods=["POST"])
@admin_required
def save_settings():
    check_csrf()
    d = load()
    s = d["settings"]
    for k in TEXT_FIELDS:
        if k in request.form:
            s[k] = request.form[k].strip() if k not in ("about", "skills", "stats") else request.form[k]
    for field in ("logo", "banner", "photo"):
        new = save_upload(field, IMG_EXT)
        if new:
            remove_file(s.get(field))
            s[field] = new
        if request.form.get("remove_" + field):
            remove_file(s.get(field))
            s[field] = ""
    save(d)
    flash("Settings saved.")
    return redirect(url_for("admin") + "#settings")


@app.route(ADMIN_PATH + "/password", methods=["POST"])
@admin_required
def change_password():
    check_csrf()
    pw = request.form.get("new_password", "")
    if len(pw) < 6:
        flash("Password must be at least 6 characters.")
    else:
        d = load()
        d["password_hash"] = generate_password_hash(pw)
        save(d)
        flash("Password changed.")
    return redirect(url_for("admin") + "#password")


@app.route(ADMIN_PATH + "/item/add", methods=["POST"])
@admin_required
def item_add():
    check_csrf()
    d = load()
    fn = save_upload("file")
    url = request.form.get("url", "").strip()
    ext = fn.rsplit(".", 1)[-1].lower() if fn else ""
    if fn:
        kind = "image" if ext in IMG_EXT else "video"
    elif url:
        kind = "link"
    else:
        flash("Please add a file or a link.")
        return redirect(url_for("admin") + "#portfolio")
    d["items"].append({
        "id": uuid.uuid4().hex[:10],
        "title": request.form.get("title", "").strip() or "Untitled",
        "description": request.form.get("description", "").strip(),
        "category": request.form.get("category", "").strip(),
        "kind": kind, "file": fn or "", "url": url,
    })
    save(d)
    flash("Added to portfolio.")
    return redirect(url_for("admin") + "#portfolio")


@app.route(ADMIN_PATH + "/item/<iid>/edit", methods=["POST"])
@admin_required
def item_edit(iid):
    check_csrf()
    d = load()
    for it in d["items"]:
        if it["id"] == iid:
            it["title"] = request.form.get("title", "").strip() or it["title"]
            it["description"] = request.form.get("description", "").strip()
            it["category"] = request.form.get("category", "").strip()
            if it["kind"] == "link":
                it["url"] = request.form.get("url", "").strip()
    save(d)
    flash("Updated.")
    return redirect(url_for("admin") + "#portfolio")


@app.route(ADMIN_PATH + "/item/<iid>/delete", methods=["POST"])
@admin_required
def item_delete(iid):
    check_csrf()
    d = load()
    for it in d["items"]:
        if it["id"] == iid:
            remove_file(it.get("file"))
    d["items"] = [i for i in d["items"] if i["id"] != iid]
    save(d)
    flash("Deleted.")
    return redirect(url_for("admin") + "#portfolio")


@app.route(ADMIN_PATH + "/item/<iid>/move/<direction>", methods=["POST"])
@admin_required
def item_move(iid, direction):
    check_csrf()
    d = load()
    ids = [i["id"] for i in d["items"]]
    if iid in ids:
        idx = ids.index(iid)
        j = idx - 1 if direction == "up" else idx + 1
        if 0 <= j < len(ids):
            d["items"][idx], d["items"][j] = d["items"][j], d["items"][idx]
            save(d)
    return redirect(url_for("admin") + "#portfolio")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
