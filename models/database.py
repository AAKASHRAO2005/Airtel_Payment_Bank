"""
Pure In-Memory Data Store for Airtel Payment Bank.
No database required — all data lives in Python dicts.
Data resets on server restart (perfectly fine for demo/dev).
"""

import threading
import datetime
from decimal import Decimal
from werkzeug.security import generate_password_hash
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class InMemoryStore:
    """Thread-safe, pure in-memory data store."""

    def __init__(self):
        self._lock = threading.Lock()
        self._counters = {
            'users': 0,
            'transactions': 0,
            'deposits': 0,
            'external_transfers': 0,
            'loans': 0,
        }
        # Tables: dict of id → record dict
        self.users = {}
        self.transactions = {}
        self.deposits = {}
        self.external_transfers = {}
        self.loans = {}

        self._seed_admin()

    # ── Internal helpers ─────────────────────────────────────

    def _next_id(self, table):
        self._counters[table] += 1
        return self._counters[table]

    @staticmethod
    def _now():
        return datetime.datetime.now()

    def _seed_admin(self):
        """Create default admin user on startup."""
        hashed = generate_password_hash("admin143", method="pbkdf2:sha256")
        admin_id = self._next_id('users')
        self.users[admin_id] = {
            'id': admin_id,
            'full_name': 'Admin Bank',
            'mobile': 'admin143',
            'password': hashed,
            'balance': Decimal('1000000.00'),
            'role': 'admin',
        }
        logger.info("✅ In-memory store initialized with admin user (mobile: admin143, password: admin143)")

    # ══════════════════════════════════════════════════════════
    #  USER OPERATIONS
    # ══════════════════════════════════════════════════════════

    def create_user(self, full_name, mobile, password_hash):
        with self._lock:
            # Enforce unique mobile
            for u in self.users.values():
                if u['mobile'] == mobile:
                    raise ValueError("Mobile number already exists")
            uid = self._next_id('users')
            self.users[uid] = {
                'id': uid,
                'full_name': full_name,
                'mobile': mobile,
                'password': password_hash,
                'balance': Decimal('0.00'),
                'role': 'user',
            }
            return uid

    def get_user_by_id(self, user_id):
        return self.users.get(user_id)

    def get_user_by_mobile(self, mobile):
        for u in self.users.values():
            if u['mobile'] == mobile:
                return u
        return None

    def get_admin_user(self):
        for u in self.users.values():
            if u['role'] == 'admin':
                return u
        return None

    def get_all_users(self):
        return list(self.users.values())

    def get_total_users(self):
        return len(self.users)

    def get_total_balance(self):
        return sum(u['balance'] for u in self.users.values())

    def update_user_name(self, user_id, full_name):
        with self._lock:
            if user_id in self.users:
                self.users[user_id]['full_name'] = full_name

    def update_user_password(self, user_id, password_hash):
        with self._lock:
            if user_id in self.users:
                self.users[user_id]['password'] = password_hash

    def adjust_balance(self, user_id, delta):
        """Add delta to user balance (negative delta = deduction)."""
        with self._lock:
            if user_id in self.users:
                self.users[user_id]['balance'] += Decimal(str(delta))

    # ══════════════════════════════════════════════════════════
    #  TRANSACTION OPERATIONS
    # ══════════════════════════════════════════════════════════

    def add_transaction(self, sender_id, receiver_id, amount, transaction_type='transfer'):
        with self._lock:
            tid = self._next_id('transactions')
            self.transactions[tid] = {
                'id': tid,
                'sender_id': sender_id,
                'receiver_id': receiver_id,
                'amount': Decimal(str(amount)),
                'status': 'success',
                'transaction_type': transaction_type,
                'timestamp': self._now(),
            }
            return tid

    def _enrich_transaction(self, t):
        """Attach sender_name and receiver_name to a transaction dict."""
        enriched = dict(t)
        sender = self.users.get(t['sender_id'])
        receiver = self.users.get(t['receiver_id'])
        enriched['sender_name'] = sender['full_name'] if sender else 'Unknown'
        enriched['receiver_name'] = receiver['full_name'] if receiver else 'Unknown'
        return enriched

    def get_user_transactions(self, user_id, limit=None):
        txns = [t for t in self.transactions.values()
                if t['sender_id'] == user_id or t['receiver_id'] == user_id]
        txns.sort(key=lambda x: x['timestamp'], reverse=True)
        if limit:
            txns = txns[:limit]
        return [self._enrich_transaction(t) for t in txns]

    def get_all_transactions(self, limit=50):
        txns = sorted(self.transactions.values(), key=lambda x: x['timestamp'], reverse=True)
        return [self._enrich_transaction(t) for t in txns[:limit]]

    def get_total_transactions(self):
        return len(self.transactions)

    def delete_transaction(self, transaction_id):
        with self._lock:
            return self.transactions.pop(transaction_id, None)

    # ══════════════════════════════════════════════════════════
    #  DEPOSIT OPERATIONS
    # ══════════════════════════════════════════════════════════

    def add_deposit(self, user_id, amount, utr):
        with self._lock:
            # Enforce unique UTR
            for d in self.deposits.values():
                if d['utr'] == utr:
                    raise ValueError("UTR already submitted")
            did = self._next_id('deposits')
            self.deposits[did] = {
                'id': did,
                'user_id': user_id,
                'amount': Decimal(str(amount)),
                'utr': utr,
                'status': 'pending',
                'timestamp': self._now(),
            }
            return did

    def get_deposit(self, deposit_id):
        return self.deposits.get(deposit_id)

    def get_pending_deposits(self):
        results = []
        for d in self.deposits.values():
            if d['status'] == 'pending':
                user = self.users.get(d['user_id'])
                enriched = dict(d)
                enriched['full_name'] = user['full_name'] if user else 'Unknown'
                enriched['mobile'] = user['mobile'] if user else 'Unknown'
                results.append(enriched)
        results.sort(key=lambda x: x['timestamp'])
        return results

    def update_deposit_status(self, deposit_id, status):
        with self._lock:
            if deposit_id in self.deposits:
                self.deposits[deposit_id]['status'] = status

    # ══════════════════════════════════════════════════════════
    #  EXTERNAL TRANSFER OPERATIONS
    # ══════════════════════════════════════════════════════════

    def add_external_transfer(self, user_id, bank_name, account_no, ifsc, amount):
        with self._lock:
            eid = self._next_id('external_transfers')
            self.external_transfers[eid] = {
                'id': eid,
                'user_id': user_id,
                'bank_name': bank_name,
                'account_no': account_no,
                'ifsc': ifsc,
                'amount': Decimal(str(amount)),
                'status': 'completed',
                'timestamp': self._now(),
            }
            return eid

    # ══════════════════════════════════════════════════════════
    #  LOAN OPERATIONS
    # ══════════════════════════════════════════════════════════

    def add_loan(self, user_id, amount_granted, amount_due):
        with self._lock:
            lid = self._next_id('loans')
            self.loans[lid] = {
                'id': lid,
                'user_id': user_id,
                'amount_granted': Decimal(str(amount_granted)),
                'amount_due': Decimal(str(amount_due)),
                'status': 'active',
                'timestamp': self._now(),
            }
            return lid

    def get_loan(self, loan_id):
        return self.loans.get(loan_id)

    def get_user_loans(self, user_id):
        loans = [l for l in self.loans.values() if l['user_id'] == user_id]
        loans.sort(key=lambda x: x['timestamp'], reverse=True)
        return loans

    def update_loan_status(self, loan_id, status):
        with self._lock:
            if loan_id in self.loans:
                self.loans[loan_id]['status'] = status


# ── Singleton instance ───────────────────────────────────────
db = InMemoryStore()
