from flask import Blueprint, render_template, request, redirect, session, flash
from services.user_service import UserService

auth_bp = Blueprint('auth', __name__)

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        full_name = request.form.get("full_name")
        mobile = request.form.get("mobile")
        password = request.form.get("password")
        
        try:
            UserService.create_user(full_name, mobile, password)
            flash("Registration Successful. Please Login 💙", "success")
            return redirect("/login")
        except Exception as e:
            flash(f"Registration Failed: Mobile number might already exist. ❌", "danger")
            return redirect("/register")

    return render_template("register.html")

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        mobile = request.form.get("mobile")
        password = request.form.get("password")

        user = UserService.authenticate_user(mobile, password)

        if user:
            session["user_id"] = user["id"]
            session["user_name"] = user["full_name"]
            session["role"] = user["role"]
            flash("Login Successful 💙", "success")
            return redirect("/dashboard")
        else:
            flash("Invalid Mobile or Password ❌", "danger")
            return redirect("/login")

    return render_template("login.html")

@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect("/login")
