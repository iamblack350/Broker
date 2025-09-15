import psycopg2
from flask import Blueprint, flash, request, redirect, render_template, session, url_for, jsonify
from sqlalchemy.exc import DatabaseError

from database import get_conn

dashboard_bp = Blueprint("dashboard", __name__, template_folder="templates")

@dashboard_bp.route("/dashboard")
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for("auth.login"))

    userid = session["user_id"]

    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT balance, firstname FROM profile WHERE userid = %s", (userid,))
    row = cursor.fetchone()
    conn.close()

    balance = 0.0
    if row:
        balance = row[0] or 0.0
        firstname = row[1]

    # static WhatsApp link (replace phone number with admin's number in international format)
    whatsapp_number = "15551234567"  # replace with real admin number, e.g. '2348012345678' without '+' or spaces
    whatsapp_link = f"https://wa.me/{whatsapp_number}?text=Hello%20Admin%20I%20want%20to%20%Invest"

    # If you render a template, pass balance and whatsapp_link to it.
    return render_template("dashboard.html", whatsapp_link = whatsapp_link,
                           balance = balance, userid = userid, firstname = firstname)


@dashboard_bp.route("/profile")
def profile():
    if "user_id" not in session:
        return redirect("/login")

    userid = session["user_id"]
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT userid, firstname, lastname, email, phone, address, nationality, balance
        FROM profile WHERE userid = %s
    """, (userid,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return "Profile not found", 404

    profile_data = {
        "userid": row[0],
        "firstname": row[1],
        "lastname": row[2],
        "email": row[3],
        "phone": row[4],
        "address": row[5],
        "nationality": row[6],
        "balance_usd": float(row[7] or 0.0)
    }
    return render_template("profile.html",profile = profile_data)

@dashboard_bp.route("/edit/<int:user_id>", methods=["GET", "POST"])
def edit(user_id):
    # Only allow editing your own profile
    if "user_id" not in session or session["user_id"] != user_id:
        return "Unauthorized", 403

    if request.method == "POST":
        firstname = request.form.get('firstname', '').strip()
        lastname = request.form.get('lastname', '').strip()
        phone = request.form.get('phone', '').strip()
        address = request.form.get('address', '').strip()
        nationality = request.form.get('nationality', '').strip()

        # get current email from profile (we keep email in sync)
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT email FROM profile WHERE userid = %s", (user_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return "Profile not found", 404
        email = row[0]

    # UPDATE profile with correct SQL and parameter order
        cursor.execute(
            "UPDATE profile SET firstname = %s, lastname = %s, phone = %s, address = %s, nationality = %s WHERE userid = %s",
            (firstname, lastname, phone, address, nationality, user_id)
        )

        conn.commit()
        conn.close()
        return redirect(url_for("dashboard.profile"))

    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT firstname, lastname, email, phone, address, nationality FROM profile WHERE userid = %s",
                   (user_id,))
    profiles = cursor.fetchone()

    profile_data = {"firstname": profiles[0],
                    "lastname": profiles[1],
                    "email": profiles[2],
                    "phone": profiles[3],
                    "address": profiles[4],
                    "nationality": profiles[5],
                    "userid": user_id}

    # GET -> show edit page (create editProfile.html)
    return render_template("editProfile.html", profile = profile_data)


@dashboard_bp.route("/withdraw", methods = ["GET", "POST"])
def withdraw():
    if "user_id" not in session:
        return "Unauthorize", 403

    id = session['user_id']
    if request.method == "POST":
        amount = request.form.get("amount","").strip()

        if amount.isalpha():
            flash("Invalid input, amount must be digits")
            return 0
        if amount == "":
            flash("Please input an amount to withdraw")
            return jsonify(error="field must not be empty")

        conn = get_conn()
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT balance FROM profile WHERE userid = %s",(id,))
            user = cursor.fetchone()
            if not user:
                return "Not found", 404

            if float(amount) > user[0]:
                flash("Insufficient funds!")
                return redirect(url_for("dashboard.withdraw"))
            current_balance = user[0] - float(amount)
            cursor.execute("UPDATE profile SET balance = %s WHERE userid = %s ", (current_balance,id))
            conn.commit()
            flash(f"You successfully withdrawn ${amount}", "success")
        except psycopg2.DatabaseError as e:
            conn.rollback()
            flash("Something Went wrong")
            conn.close()
            return redirect(url_for("dashboard.withdraw"))
        conn.close()
        return redirect(url_for("dashboard.dashboard"))
    conn = get_conn()
    detail = ()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT balance FROM profile WHERE userid = %s",(id,))
        detail = cursor.fetchone()
        conn.close()
    except DatabaseError:
        conn.rollback()
        conn.close()
    return render_template("withdraw.html", balance=detail[0])
