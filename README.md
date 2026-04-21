# 🏦 TR Payment Bank (Full Stack Project)

A modern **Digital Banking Web Application** built using **Flask, MySQL/PostgreSQL/SQLite, and Docker**.
This project simulates real-world banking features like money transfer, deposits, transaction history, and admin control. It features a robust multi-database fallback system out of the box.

---

## 🚀 Features

### 👤 User Features
* 🔐 Register & Login system
* 💰 Check account balance
* 💸 Transfer money to other users (Internal & External Bank Transfers)
* 💳 Apply for instant loans
* ➕ Add money via QR (UPI simulation)
* 📜 Transaction history
* 📄 Download bank statement (PDF)
* 👤 Profile management (update name & password)

### 🏦 Admin Features
* 👑 Admin dashboard
* 📊 View all users & transactions
* ✓ Approve/Reject deposit requests
* 🗑 Delete transaction history
* 💰 Monitor total bank balance

### 🎨 UI Features
* 📱 Modern glassmorphism banking dashboard
* 📊 Interactive UI with animations
* 🌙 Dark mode support
* 📌 Responsive Sidebar navigation

---

## ⚙️ Installation & Setup (Local Setup)

### 1️⃣ Clone Repository
```bash
git clone https://github.com/yourusername/tr_payment_bank.git
cd tr_payment_bank
```

### 2️⃣ Create Virtual Environment & Install Requirements
We recommend using a Python virtual environment to manage dependencies:
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

---

## 🗄️ Database Setup & Connection

This application features an advanced **Triple-layered Database Abstraction**. It will automatically try to connect in this order:
1. **Primary**: MySQL Server
2. **Secondary**: Supabase (PostgreSQL)
3. **Fallback**: Local zero-config SQLite (`airtel_local.db` / `tr_local.db`)

You do **not** need to manually build schema tables. The application automatically initializes the database tables (Users, Transactions, Deposits, Loans) on startup!

### How to Create & Connect

To use the primary MySQL or secondary Supabase databases, you must set the variables in a `.env` file at the root of the project. Simply copy `.env.example` to `.env` and fill it out:

```bash
cp .env.example .env
```

#### Option A: MySQL (Recommended)
You must first create the database on your MySQL server:
```sql
CREATE DATABASE tr_payment_bank;
```
Then update your `.env` connection settings:
```env
MYSQL_HOST=localhost
MYSQL_USER=your_user
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=tr_payment_bank
MYSQL_PORT=3306
```

#### Option B: Supabase / PostgreSQL
Obtain your Postgres connection URL from Supabase and add it to your `.env`:
```env
SUPABASE_DB_URL=postgresql://postgres:[YOUR-PASSWORD]@db.xxxx.supabase.co:5432/postgres
```

#### Option C: SQLite (No setup required!)
If neither MySQL nor Postgres credentials are provided in `.env` (or if those connections fail), the app seamlessly and automatically falls back to SQLite. It will create a local `.db` file in the database directory dynamically.

---

## 🏃‍♂️ How to Run

### Local Development Server
Make sure your virtual environment is activated, then simply run:
```bash
python app.py
```
Open your browser and navigate to: `http://localhost:5000`

### Running via Docker Compose
To run the full stack (App + fully configured MySQL Database) via Docker:
```bash
docker-compose up --build
```
This automatically provisions a MySQL container, sets up the databases, runs the app, and exposes it on port `5000`.

---

## 📘 How to Use

1. **Sign up**: Create an account on the Registration page.
2. **Login**: Use your phone number and password to enter the dashboard.
3. **Admin Privileges**: The first time the database initializes, an Admin account is created behind the scenes. If using the default setup, you can perform simulated actions (like Deposits and Loans) which impact the bank's internal mock reserves. To access the admin panel, login as the admin user (credentials hardcoded in DB setup) or upgrade an existing user's role to 'admin' manually in the database.
4. **Deposit Money**: Head to the "Deposit / Add Money" section, simulate a UTR transaction, and have the admin approve it (or login as Admin to approve it).
5. **Transfers**: Explore the "Transfer" section to securely send mock funds to other registered users seamlessly!

---

## 🔐 Future Improvements
* 🔑 OTP verification system
* 📲 Real payment gateway integration
* 📊 Advanced analytics dashboard
* 🔒 Security enhancements (JWT, encryption)
* ☁️ Cloud deployment (Vercel / Render)

## 👨‍💻 Author
**Tukaram Gore**
