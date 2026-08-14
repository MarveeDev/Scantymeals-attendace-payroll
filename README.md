# ScantyMeals Staff Attendance & Payroll System

A production-ready standalone web application built for ScantyMeals to manage worker details, manual attendance, and dynamically calculate payroll securely.

## Features
- **Secure Admin Dashboard:** Centralized view of all active workers and daily attendance stats.
- **Worker Lifecycle Management:** Full CRUD operations with support for deactivation without deleting historical records.
- **Manual Attendance Tracking:** Daily manual "Present" or "Absent" marking for all active staff.
- **Dynamic Payroll Generation:** Accurate gross and net payroll generation based on integer/pesewa arithmetic with configurable absence deduction strategies. Overlapping finalized payroll protection is built-in.
- **Payment Tracking:** Log all salary payouts across different methods (Cash, MoMo, Bank).
- **Reports:** View and export attendance reports in CSV format.
- **Audit Logs:** Full administrative action tracking securely stored.

## Architecture
- **Backend:** Python + Flask
- **Database:** MongoDB Atlas (via PyMongo)
- **Timezone:** Fixed to `Africa/Accra` using `zoneinfo`.
- **Frontend:** Server-side rendered HTML using Jinja2 templates and rich Vanilla CSS.

---

## Local Installation

1. **Clone the repository and enter the directory.**
2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Or `.\venv\Scripts\Activate.ps1` on Windows
   ```
3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Configure Environment Variables:**
   Copy `.env.example` to `.env` and fill in the details:
   ```env
   MONGODB_URI=mongodb://localhost:27017/ # Or your Atlas connection string
   MONGODB_DATABASE=scantymeals_staff
   SECRET_KEY=your_secure_secret_key
   ADMIN_USERNAME=admin
   ADMIN_PASSWORD=admin123
   APP_TIMEZONE=Africa/Accra
   ```
5. **Run the application:**
   ```bash
   python app.py
   ```
   The application will be accessible at `http://localhost:5000`.

---

## MongoDB Atlas Setup
1. Create a free cluster on MongoDB Atlas.
2. Go to **Database Access** and create a new user (store the username and password).
3. Go to **Network Access** and add `0.0.0.0/0` to allow connections from anywhere (required for Render).
4. Go to **Databases** > **Connect** > **Drivers** and copy your connection string.
5. Replace `<password>` in the connection string and use it as your `MONGODB_URI`.

---

## Render Deployment

1. Push this codebase to a GitHub repository.
2. Log into [Render](https://render.com) and click **New > Web Service**.
3. Connect your GitHub repository.
4. **Build Command:** `pip install -r requirements.txt`
5. **Start Command:** `gunicorn app:app`
6. Open the **Environment** section and add the following Environment Variables:
   - `MONGODB_URI` (Your Atlas URI)
   - `MONGODB_DATABASE` (e.g. scantymeals_staff)
   - `SECRET_KEY` (Generate a random string)
   - `ADMIN_USERNAME` (Your preferred admin login)
   - `ADMIN_PASSWORD` (Your preferred admin password)
   - `APP_TIMEZONE` (`Africa/Accra`)
7. Click **Deploy Web Service**.

> **Note:** The application uses `gunicorn` for the production server on Render. The initial admin account will be automatically created on the first successful startup if it does not already exist.
