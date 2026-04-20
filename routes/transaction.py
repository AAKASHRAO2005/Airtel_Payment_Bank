import io
import uuid
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, session, flash, send_file
from decimal import Decimal, InvalidOperation

# reportlab is optional — PDF statement download needs it
try:
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib import pagesizes
    HAS_REPORTLAB = True
except (ImportError, OSError):
    HAS_REPORTLAB = False

from services.user_service import UserService
from services.transaction_service import TransactionService

transaction_bp = Blueprint('transaction', __name__)

@transaction_bp.route("/transfer-page", methods=["GET"])
def transfer_page():
    if "user_id" not in session:
        return redirect("/login")

    sender_id = session["user_id"]
    sender = UserService.get_user_by_id(sender_id)
    return render_template("transfer.html", balance=sender["balance"])

@transaction_bp.route("/transfer", methods=["POST"])
def transfer():
    if "user_id" not in session:
        return redirect("/login")

    sender_id = session["user_id"]

    if request.method == "POST":
        receiver_mobile = request.form.get("receiver_mobile")
        try:
            amount = Decimal(request.form.get("amount", "0")).quantize(Decimal('0.01'))
        except InvalidOperation:
            amount = Decimal('0.00')

        success, msg_or_name = TransactionService.transfer_money(sender_id, receiver_mobile, amount)
        
        if success:
            return render_template("transfer_success.html", amount=amount, receiver_name=msg_or_name)
        else:
            flash(f"Transfer Failed: {msg_or_name} ❌", "danger")
            return redirect("/transfer-page")

@transaction_bp.route("/deposit-page", methods=["GET"])
def deposit_page():
    if "user_id" not in session:
        return redirect("/login")
    return render_template("deposit.html")

@transaction_bp.route("/deposit", methods=["POST"])
def deposit():
    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":
        user_id = session["user_id"]
        try:
            amount = Decimal(request.form.get("amount", "0")).quantize(Decimal('0.01'))
        except InvalidOperation:
            amount = Decimal('0.00')
        utr = request.form.get("utr", "")

        success, msg = TransactionService.create_deposit_request(user_id, amount, utr)
        
        if success:
            flash(msg, "success")
            return redirect("/dashboard")
        else:
            flash(f"Deposit Failed: {msg} ❌", "danger")
            return redirect("/deposit-page")

@transaction_bp.route("/download-statement")
def download_statement():
    if "user_id" not in session:
        return redirect("/login")

    if not HAS_REPORTLAB:
        flash("PDF generation is temporarily unavailable.", "warning")
        return redirect("/history")

    user_id = session["user_id"]
    user = UserService.get_user_by_id(user_id)
    transactions = TransactionService.get_user_transactions(user_id)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=pagesizes.A4)
    elements = []
    styles = getSampleStyleSheet()

    elements.append(Paragraph("<b>TR Payments Bank - Statement</b>", styles["Title"]))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"Account Holder: {user['full_name']}", styles["Normal"]))
    elements.append(Paragraph(f"Generated On: {datetime.now().strftime('%d %b %Y %I:%M %p')}", styles["Normal"]))
    elements.append(Spacer(1, 20))

    data = [["Sender", "Receiver", "Amount (Rs)", "Date"]]
    for t in transactions:
        data.append([
            t["sender_name"],
            t["receiver_name"],
            str(t["amount"]),
            str(t["timestamp"])
        ])

    table = Table(data)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor('#e63946')),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey)
    ]))
    
    elements.append(table)
    doc.build(elements)
    buffer.seek(0)

    return send_file(buffer, as_attachment=True, download_name="statement.pdf", mimetype="application/pdf")

@transaction_bp.route("/bank-transfer-page", methods=["GET"])
def bank_transfer_page():
    if "user_id" not in session:
        return redirect("/login")
    balance = UserService.get_user_by_id(session["user_id"])["balance"]
    return render_template("bank_transfer.html", balance=balance)

@transaction_bp.route("/bank-transfer", methods=["POST"])
def bank_transfer():
    if "user_id" not in session:
        return redirect("/login")
        
    if request.method == "POST":
        user_id = session["user_id"]
        bank_name = request.form.get("bank_name", "")
        account_no = request.form.get("account_no", "")
        ifsc = request.form.get("ifsc", "")
        try:
            amount = Decimal(request.form.get("amount", "0")).quantize(Decimal('0.01'))
        except InvalidOperation:
            amount = Decimal('0.00')

        success, msg = TransactionService.external_bank_transfer(user_id, bank_name, account_no, ifsc, amount)
        if success:
            flash("Bank transfer initiated successfully!", "success")
            return redirect("/dashboard")
        else:
            flash(f"Transfer Failed: {msg} ❌", "danger")
            return redirect("/bank-transfer-page")

@transaction_bp.route("/loan-page", methods=["GET"])
def loan_page():
    if "user_id" not in session:
        return redirect("/login")
    user_id = session["user_id"]
    balance = UserService.get_user_by_id(user_id)["balance"]
    loans = TransactionService.get_user_loans(user_id)
    return render_template("loan.html", balance=balance, loans=loans)

@transaction_bp.route("/loan", methods=["POST"])
def loan():
    if "user_id" not in session:
        return redirect("/login")
        
    user_id = session["user_id"]
    if request.method == "POST":
        action = request.form.get("action")
        
        if action == "apply":
            try:
                amount = Decimal(request.form.get("amount", "0")).quantize(Decimal('0.01'))
            except InvalidOperation:
                amount = Decimal('0.00')
            success, msg = TransactionService.apply_for_loan(user_id, amount)
            if success:
                flash("Loan approved and credited instantly! 🎉", "success")
            else:
                flash(f"Loan Application Failed: {msg} ❌", "danger")
        elif action == "repay":
            loan_id = request.form.get("loan_id")
            success, msg = TransactionService.repay_loan(user_id, loan_id)
            if success:
                flash("Loan repaid successfully!", "success")
            else:
                flash(f"Repayment Failed: {msg} ❌", "danger")
                
        return redirect("/loan-page")
