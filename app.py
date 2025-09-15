from flask import Flask, render_template
import os
from dotenv import load_dotenv
from dashboard import dashboard_bp
from auth import auth_bp
from database import init_db


load_dotenv()
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev_secret")

@app.route("/")
def landingPage():
    return render_template("landingPage.html")

app.register_blueprint(auth_bp, url_prefix="/auth")
app.register_blueprint(dashboard_bp, url_prefix="/dashboard")


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
