from flask import Blueprint, render_template, request, redirect, session, flash
from services.user_service import UserService
from services.transaction_service import TransactionService

user_bp = Blueprint('user', __name__)

@user_bp.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]
    user = UserService.get_user_by_id(user_id)
    
    if not user:
        session.clear()
        return redirect("/login")

    transactions = TransactionService.get_user_transactions(user_id, limit=5)
    all_transactions = TransactionService.get_user_transactions(user_id)

    total_deposit = sum(float(t['amount']) for t in all_transactions if t['receiver_id'] == user_id and t['sender_id'] != user_id)
    total_sent = sum(float(t['amount']) for t in all_transactions if t['sender_id'] == user_id and t['receiver_id'] != user_id)

    return render_template(
        "dashboard.html",
        user=user,
        name=user["full_name"],
        balance=user["balance"],
        role=user["role"],
        transactions=transactions,
        total_deposit=total_deposit,
        total_sent=total_sent,
        total_transactions=len(all_transactions)
    )

@user_bp.route("/profile", methods=["GET", "POST"])
def profile():
    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]
    user = UserService.get_user_by_id(user_id)

    if request.method == "POST":
        if "update_profile" in request.form:
            full_name = request.form.get("full_name")
            UserService.update_profile(user_id, full_name)
            flash("Profile Updated Successfully 💙", "success")
            return redirect("/profile")

        if "change_password" in request.form:
            current_password = request.form.get("current_password")
            new_password = request.form.get("new_password")
            confirm_password = request.form.get("confirm_password")

            if new_password != confirm_password:
                flash("New passwords do not match ❌", "danger")
                return redirect("/profile")

            success = UserService.change_password(user_id, current_password, new_password)
            if success:
                flash("Password Changed Successfully 🔐", "success")
            else:
                flash("Current password is incorrect ❌", "danger")
            
            return redirect("/profile")

    return render_template("profile.html", user=user)

@user_bp.route("/history")
def history():
    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]
    transactions = TransactionService.get_user_transactions(user_id)

    return render_template("history.html", transactions=transactions, user_id=user_id)
