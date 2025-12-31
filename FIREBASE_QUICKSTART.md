# 🚀 Firebase Quick Start Guide

## ✅ What's Already Done

I've set up Firebase integration for you! Here's what's ready:

### Files Created:
1. ✅ `FIREBASE_SETUP.md` - Complete setup guide
2. ✅ `utils/firebase_storage.py` - Firebase utility functions
3. ✅ `test_firebase.py` - Test script
4. ✅ Updated `requirements.txt` with `firebase-admin`
5. ✅ Updated `.gitignore` to protect credentials
6. ✅ Updated `.env.example` with Firebase placeholders

---

## 📋 Next Steps (Do This Now!)

### Step 1: Create Firebase Project (5 minutes)
1. Go to https://console.firebase.google.com/
2. Click "Add Project"
3. Name it: `roomies-platform`
4. Disable Google Analytics (optional)
5. Click "Create Project"

### Step 2: Enable Firebase Storage (2 minutes)
1. In Firebase Console → **Build → Storage**
2. Click "Get Started"
3. Choose "Start in production mode"
4. Select location: **asia-south1** (Mumbai/India)
5. Click "Done"

### Step 3: Get Credentials (3 minutes)
1. Click ⚙️ (Settings) → **Project Settings**
2. Go to **Service Accounts** tab
3. Click **"Generate new private key"**
4. A JSON file will download
5. Rename it to: `firebase-credentials.json`
6. Move it to your project root: `c:\D-Drive\Roomies\roomies-demo\`

### Step 4: Update .env File
Add these two lines to your `.env` file:
```env
FIREBASE_CREDENTIALS_PATH=firebase-credentials.json
FIREBASE_STORAGE_BUCKET=roomies-platform.appspot.com
```
(Replace `roomies-platform` with YOUR project ID)

### Step 5: Test It!
Run:
```bash
python test_firebase.py
```

You should see: ✅ FIREBASE IS READY TO USE!

---

## 💡 How to Use Firebase

### Upload Room Images:
```python
from utils.firebase_storage import upload_file_to_firebase

# In your Flask route
@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['image']
    url = upload_file_to_firebase(file, folder='room-images')
    return jsonify({'url': url})
```

### Upload Verification Documents:
```python
student_id = request.files['student_id']
url = upload_file_to_firebase(student_id, folder='verification/student-ids')
```

---

## 🔐 Before Pushing to GitHub

### Double-check:
```bash
# Make sure these are in .gitignore
cat .gitignore | findstr firebase
```

Should show:
```
firebase-credentials.json
*-firebase-adminsdk-*.json
```

### Safe to commit:
- ✅ `FIREBASE_SETUP.md`
- ✅ `utils/firebase_storage.py`
- ✅ `test_firebase.py`
- ✅ `.env.example`
- ✅ `requirements.txt`

### NEVER commit:
- ❌ `.env`
- ❌ `firebase-credentials.json`

---

## 📊 Firebase Free Tier Limits

You get **FREE**:
- 5 GB Storage
- 1 GB/day Downloads
- Perfect for ~500-1000 users
- No credit card required initially

---

## 🆘 Troubleshooting

**"Firebase credentials not found"**
→ Make sure `firebase-credentials.json` is in the project root

**"Storage bucket not found"**
→ Check `FIREBASE_STORAGE_BUCKET` in `.env` matches your project

**"Authentication failed"**
→ Re-download credentials from Firebase Console

---

Need help? Check `FIREBASE_SETUP.md` for detailed instructions!
