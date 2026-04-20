from models.database import db
from services.user_service import UserService
from decimal import Decimal
import logging

logger = logging.getLogger("transaction_service")
logger.setLevel(logging.INFO)

MAX_TRANSACTION_LIMIT = Decimal("1000000.00")  # ₹10 Lakhs max per transaction


class TransactionService:
    # ── Read operations ──────────────────────────────────────

    @staticmethod
    def get_user_transactions(user_id, limit=None):
        return db.get_user_transactions(user_id, limit=limit)

    @staticmethod
    def get_all_transactions(limit=50):
        return db.get_all_transactions(limit=limit)

    @staticmethod
    def get_total_transactions_count():
        return db.get_total_transactions()

    # ── Money Transfer ───────────────────────────────────────

    @staticmethod
    def transfer_money(sender_id, receiver_mobile, amount):
        if amount <= 0:
            return False, "Invalid amount"

        if amount > MAX_TRANSACTION_LIMIT:
            return False, "Security Alert: Amount exceeds transaction limit of ₹10,00,000."

        # Get Sender
        sender = UserService.get_user_by_id(sender_id)
        if not sender:
            return False, "Sender account not found"
        if Decimal(str(sender['balance'])) < amount:
            return False, "Insufficient balance"

        # Get Receiver
        receiver = db.get_user_by_mobile(receiver_mobile)
        if not receiver:
            return False, "Receiver not found"

        if sender_id == receiver['id']:
            return False, "Cannot send money to yourself"

        try:
            # Deduct from sender, add to receiver
            db.adjust_balance(sender_id, -amount)
            db.adjust_balance(receiver['id'], amount)
            # Record transaction
            db.add_transaction(sender_id, receiver['id'], amount, 'transfer')

            logger.info(f"Transfer SUCCESS: UID {sender_id} sent ₹{amount} to UID {receiver['id']}")
            return True, receiver['full_name']

        except Exception as e:
            # Attempt to reverse the balance changes
            try:
                db.adjust_balance(sender_id, amount)
                db.adjust_balance(receiver['id'], -amount)
            except Exception:
                pass
            logger.error(f"Transfer FAILED: {str(e)}")
            return False, str(e)

    # ── Deposit Request ──────────────────────────────────────

    @staticmethod
    def create_deposit_request(user_id, amount, utr):
        if amount <= 0:
            return False, "Invalid Amount"

        if amount > MAX_TRANSACTION_LIMIT:
            return False, "Security Alert: Deposit amount exceeds limit of ₹10,00,000. Please contact your branch."

        admin = UserService.get_admin_user()
        if not admin:
            return False, "Admin account not found for simulation"

        admin_id = admin["id"]

        if user_id == admin_id:
            return False, "Admin cannot deposit using this method"

        try:
            db.add_deposit(user_id, amount, utr)
            logger.info(f"Deposit Created: UID {user_id} requested ₹{amount} (UTR: {utr})")
            return True, "Deposit request submitted successfully. Pending Admin verification."

        except ValueError as e:
            return False, "UTR has already been submitted for a deposit. Please wait for verification."
        except Exception as e:
            logger.error(f"Deposit Creation FAILED: {str(e)}")
            return False, str(e)

    # ── Approve / Reject Deposits ────────────────────────────

    @staticmethod
    def approve_deposit(deposit_id):
        deposit = db.get_deposit(deposit_id)
        if not deposit or deposit['status'] != 'pending':
            return False, "Deposit not found or already processed"

        amount = deposit['amount']
        user_id = deposit['user_id']

        admin = UserService.get_admin_user()
        if not admin:
            return False, "Admin account not found"
        admin_id = admin['id']

        try:
            # Add to admin pool (bank reserves increase from external UPI deposit)
            db.adjust_balance(admin_id, amount)
            # Add to user
            db.adjust_balance(user_id, amount)
            # Insert transaction record (admin → user deposit)
            db.add_transaction(admin_id, user_id, amount, 'deposit')
            # Update deposit status
            db.update_deposit_status(deposit_id, 'approved')

            logger.info(f"Deposit APPROVED: Deposit #{deposit_id} ₹{amount} for UID {user_id}")
            return True, "Deposit Approved"
        except Exception as e:
            logger.error(f"Deposit Approval FAILED: {str(e)}")
            return False, str(e)

    @staticmethod
    def reject_deposit(deposit_id):
        try:
            db.update_deposit_status(deposit_id, 'rejected')
            return True, "Deposit rejected"
        except Exception as e:
            return False, str(e)

    @staticmethod
    def get_pending_deposits():
        return db.get_pending_deposits()

    # ── Delete Transaction (Admin) ───────────────────────────

    @staticmethod
    def delete_transaction(transaction_id):
        """Delete a transaction record and reverse the balance changes."""
        txn = None
        # Peek at the transaction before deleting
        if transaction_id in db.transactions:
            txn = dict(db.transactions[transaction_id])

        if not txn:
            return

        try:
            amount = txn['amount']
            # Reverse: give money back to sender, take from receiver
            db.adjust_balance(txn['sender_id'], amount)
            db.adjust_balance(txn['receiver_id'], -amount)
            # Delete the record
            db.delete_transaction(transaction_id)
            logger.info(f"Transaction #{transaction_id} DELETED and balances reversed (₹{amount})")
        except Exception as e:
            logger.error(f"Transaction delete FAILED: {str(e)}")

    # ── External Bank Transfer ───────────────────────────────

    @staticmethod
    def external_bank_transfer(user_id, bank_name, account_no, ifsc, amount):
        if amount <= 0:
            return False, "Invalid Amount"
        if amount > MAX_TRANSACTION_LIMIT:
            return False, "Amount exceeds transfer limit."

        user = UserService.get_user_by_id(user_id)
        if not user:
            return False, "User account not found"
        if Decimal(str(user['balance'])) < amount:
            return False, "Insufficient balance"

        admin = UserService.get_admin_user()
        if not admin:
            return False, "System bank not available"

        # Check admin has enough reserves for outgoing transfer
        if Decimal(str(admin['balance'])) < amount:
            return False, "Bank reserves temporarily insufficient for this transfer amount"

        try:
            # Deduct from user
            db.adjust_balance(user_id, -amount)
            # Deduct from admin (bank reserves leaving system)
            db.adjust_balance(admin['id'], -amount)
            # Insert into external_transfers
            db.add_external_transfer(user_id, bank_name, account_no, ifsc, amount)

            logger.info(f"External Transfer SUCCESS: UID {user_id} sent ₹{amount} to {bank_name} ({account_no})")
            return True, "Bank Transfer Initiated Successfully"
        except Exception as e:
            logger.error(f"External Transfer FAILED: {str(e)}")
            return False, str(e)

    # ── Loans ────────────────────────────────────────────────

    @staticmethod
    def apply_for_loan(user_id, amount):
        if amount <= 0:
            return False, "Invalid loan amount"
        if amount > 50000:
            return False, "Maximum instant loan allowed is ₹50,000"

        admin = UserService.get_admin_user()
        if not admin:
            return False, "System resources temporarily unavailable for loans"
        if Decimal(str(admin['balance'])) < amount:
            return False, "System resources temporarily unavailable for loans"

        amount_due = (Decimal(str(amount)) * Decimal('1.05')).quantize(Decimal('0.01'))  # 5% flat interest

        try:
            # Deduct from admin
            db.adjust_balance(admin['id'], -amount)
            # Credit user
            db.adjust_balance(user_id, amount)
            # Log as standard transaction from admin to user
            db.add_transaction(admin['id'], user_id, amount, 'loan')
            # Create Loan record
            db.add_loan(user_id, amount, amount_due)

            logger.info(f"Loan GRANTED: UID {user_id} received ₹{amount}, due ₹{amount_due}")
            return True, "Loan granted successfully"
        except Exception as e:
            logger.error(f"Loan Application FAILED: {str(e)}")
            return False, str(e)

    @staticmethod
    def repay_loan(user_id, loan_id):
        loan_id = int(loan_id)
        loan = db.get_loan(loan_id)
        if not loan or loan['user_id'] != user_id or loan['status'] != 'active':
            return False, "Loan not found or already repaid"

        amount_due = Decimal(str(loan['amount_due']))
        user = UserService.get_user_by_id(user_id)
        if not user or Decimal(str(user['balance'])) < amount_due:
            return False, "Insufficient balance to repay loan"

        admin = UserService.get_admin_user()
        if not admin:
            return False, "System bank account not found"

        try:
            # Deduct from user
            db.adjust_balance(user_id, -amount_due)
            # Send back to admin
            db.adjust_balance(admin['id'], amount_due)
            # Log repayment transaction
            db.add_transaction(user_id, admin['id'], amount_due, 'loan_repayment')
            # Update loan status
            db.update_loan_status(loan_id, 'repaid')

            logger.info(f"Loan REPAID: UID {user_id} repaid ₹{amount_due} for Loan #{loan_id}")
            return True, "Loan repaid successfully"
        except Exception as e:
            logger.error(f"Loan Repayment FAILED: {str(e)}")
            return False, str(e)

    @staticmethod
    def get_user_loans(user_id):
        return db.get_user_loans(user_id)
