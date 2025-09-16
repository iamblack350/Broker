from flask import Blueprint, flash, render_template, request, session, redirect, url_for
import bcrypt
import psycopg2
from core.database import get_conn




auth_bp = Blueprint("auth", __name__, template_folder="templates")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        firstname = request.form.get('firstname', '').strip()
        lastname = request.form.get('lastname', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not (firstname and lastname and email and password):
            flash("All fields are required.")
            return redirect(url_for("auth.register"))

        # Hash the password using bcrypt
        salt = bcrypt.gensalt()
        password_bytes = password.encode("utf-8")
        hashed_password = bcrypt.hashpw(password_bytes, salt)

        conn = get_conn()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO users(firstname, lastname, email, password) VALUES(%s,%s,%s,%s) RETURNING id",
                (firstname, lastname, email, hashed_password)
            )
            userid = cursor.fetchone()[0]

            # create profile with default balance 0.0
            cursor.execute(
                "INSERT INTO profile(userid, firstname, lastname, email, balance) VALUES(%s,%s,%s,%s,%s)",
                (userid, firstname, lastname, email, 0.0)
            )
            conn.commit()
        except psycopg2.IntegrityError as e:
            conn.rollback()
            # unique constraint errors (email already exists)
            flash("Email already registered.")
            conn.close()
            return redirect(url_for("auth.register"))
        conn.close()
        return redirect(url_for("auth.login"))

    return render_template("register.html")

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT id, password FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        conn.close()

        if not user:
            flash("Invalid credentials.")
            return redirect(url_for("auth.login"))

        user_id = user[0]


        password_bytes = password.encode("utf-8")
        try:
            if bcrypt.checkpw(password_bytes, user[1].tobytes()):
                session['user_id'] = user_id
                session['email'] = email
                return redirect(url_for("dashboard.dashboard"))
            else:
                flash("Invalid credentials.")
        except ValueError:
            # bcrypt raises if stored hash malformed
            flash("Authentication error.")
        return redirect(url_for("auth.login"))

    return render_template("login.html")

@auth_bp.route("/logout")
def logout():
    session.pop("email", None)
    session.pop("user_id", None)
    return redirect(url_for("auth.login"))

@auth_bp.route("/forgotten-password")
def forgotten_password():
    pass