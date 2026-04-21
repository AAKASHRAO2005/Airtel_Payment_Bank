from flask import Flask, redirect
from werkzeug.exceptions import HTTPException
from config.settings import settings

# Initialize application
app = Flask(__name__)
app.secret_key = settings.SECRET_KEY

# Register Blueprints
from routes.auth import auth_bp
from routes.user import user_bp
from routes.transaction import transaction_bp
from routes.admin import admin_bp
from routes.api import api_bp

app.register_blueprint(auth_bp)
app.register_blueprint(user_bp)
app.register_blueprint(transaction_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(api_bp, url_prefix='/api')

@app.route("/")
def home():
    return redirect("/login")

@app.errorhandler(Exception)
def handle_exception(e):
    # Pass through HTTP errors
    if isinstance(e, HTTPException):
        return e

    error_message = str(e)
    return f"<h1>Internal Server Error</h1><p>{error_message}</p>", 500

if __name__ == "__main__":
  app.run(debug=True, port=8080)