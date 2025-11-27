# 🚀 Deployment Guide: Roomies on Render + Supabase

This guide will help you deploy the Roomies application to Render.com (Backend) and Supabase (Database).

## 📋 Prerequisites

1.  **GitHub Account**: Your code must be pushed to a GitHub repository.
2.  **Render.com Account**: For hosting the Python backend.
3.  **Supabase Account**: For hosting the PostgreSQL database.

---

## 1️⃣ Prepare Your Code (Already Done)

I have already performed the following steps for you:
*   ✅ Added `gunicorn` and `psycopg2-binary` to `requirements.txt`.
*   ✅ Added `Procfile` for Render.
*   ✅ Updated `app.py` to handle PostgreSQL connection strings.
*   ✅ Created `.gitignore` to exclude unnecessary files.

**Next Step:**
1.  Delete `app_new.py` (it's a backup file).
2.  Commit and push all changes to your GitHub repository.

---

## 2️⃣ Setup Supabase (Database)

1.  Go to [Supabase.com](https://supabase.com/) and sign in.
2.  Click **"New Project"**.
3.  Enter a Name (e.g., `roomies-db`) and a strong Database Password (save this!).
4.  Choose a Region close to you (e.g., Mumbai).
5.  Click **"Create new project"**.
6.  Wait for the database to set up (takes ~2 mins).
7.  Once ready, go to **Project Settings** (cog icon) -> **Database**.
8.  Under **Connection string**, select **URI** mode.
9.  Copy the connection string. It looks like:
    `postgresql://postgres:[YOUR-PASSWORD]@db.xyz.supabase.co:5432/postgres`
10. **Replace `[YOUR-PASSWORD]`** with the password you created in step 3.
    *   *Note: If your password has special characters, you might need to URL encode them.*

---

## 3️⃣ Deploy to Render (Backend)

1.  Go to [Render.com](https://render.com/) and sign in.
2.  Click **"New +"** -> **"Web Service"**.
3.  Connect your GitHub repository.
4.  **Configure the service:**
    *   **Name:** `roomies-app` (or similar)
    *   **Region:** Singapore (closest to India)
    *   **Branch:** `main` (or master)
    *   **Runtime:** `Python 3`
    *   **Build Command:** `pip install -r requirements.txt`
    *   **Start Command:** `gunicorn app:app`
    *   **Plan:** Free

5.  **Environment Variables (Advanced):**
    Scroll down to "Environment Variables" and add the following:

    | Key | Value |
    | :--- | :--- |
    | `DATABASE_URL` | Paste your Supabase connection string here |
    | `SECRET_KEY` | Generate a random string (e.g., `super-secret-key-123`) |
    | `PYTHON_VERSION` | `3.10.0` (Recommended) |

6.  Click **"Create Web Service"**.

---

## 4️⃣ Initialize the Database on Render

Once the deployment finishes, your database will be empty. You need to create the tables.

1.  In the Render Dashboard, go to your Web Service.
2.  Click on the **"Shell"** tab (on the left).
3.  Wait for the terminal to connect.
4.  Run the reset script to create tables:
    ```bash
    python reset_db.py
    ```
    *   Type `yes` when prompted.
5.  (Optional) Populate initial data:
    ```bash
    python populate_real_data.py
    ```

---

## ⚠️ Important Notes & Limitations

1.  **File Uploads**:
    *   Render's free tier filesystem is **ephemeral**. This means any files uploaded (ID cards, profile pics) will be **DELETED** every time the app restarts or redeploys.
    *   **Solution**: For a production app, you must use a cloud storage service like AWS S3, Google Cloud Storage, or Cloudinary to store user uploads.

2.  **AI/Chat Features**:
    *   You mentioned these won't work. The code is still there, but if `easyocr` or `opencv` tries to run heavy tasks, the Render free tier instance (512MB RAM) might crash (OOM - Out Of Memory).
    *   If the deployment fails during `pip install`, you might need to remove `easyocr` and `opencv-python-headless` from `requirements.txt` and disable those features in the code.

3.  **Database Latency**:
    *   Since the app is on Render (Singapore) and DB is on Supabase (Mumbai), there might be slight latency. This is normal for free tier setups.
