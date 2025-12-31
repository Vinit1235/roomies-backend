# 🔥 Firebase Integration Guide for Roomies

This guide shows you how to integrate Firebase into your Roomies Flask application using the **FREE Spark Plan**.

## 🎯 What We'll Use Firebase For

1. **Firebase Storage** - Store user-uploaded images (room photos, ID cards, documents)
2. **Firebase Authentication (Optional)** - Alternative to Flask-Login
3. **Firestore Database (Optional)** - Real-time database alternative to SQLite
4. **Firebase Cloud Messaging** - Push notifications for bookings/updates

---

## 📋 Step 1: Create Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click **"Add Project"**
3. Project name: `roomies-platform` (or your choice)
4. Disable Google Analytics (optional for free tier)
5. Click **"Create Project"**

---

## 📦 Step 2: Enable Firebase Services

### A. Enable Firebase Storage (For Image Uploads)
1. In Firebase Console, go to **Build → Storage**
2. Click **"Get Started"**
3. Choose **"Start in production mode"** (we'll set rules later)
4. Select location: `asia-south1` (Mumbai) or nearest to you
5. Click **"Done"**

### B. Update Storage Rules
Go to **Storage → Rules** and paste:
```javascript
rules_version = '2';
service firebase.storage {
  match /b/{bucket}/o {
    // Allow uploads up to 10MB for authenticated users
    match /{allPaths=**} {
      allow read: if true;
      allow write: if request.auth != null 
                   && request.resource.size < 10 * 1024 * 1024;
    }
  }
}
```

### C. Enable Firestore (Optional - for real-time features)
1. Go to **Build → Firestore Database**
2. Click **"Create database"**
3. Choose **"Start in production mode"**
4. Select location: `asia-south1`

---

## 🔑 Step 3: Get Firebase Credentials

### For Backend (Python/Flask):
1. In Firebase Console, click **⚙️ (Settings) → Project Settings**
2. Go to **Service Accounts** tab
3. Click **"Generate new private key"**
4. Save the JSON file as `firebase-credentials.json`
5. **IMPORTANT**: Move it to your project root but **DON'T commit to Git!**

### For Frontend (JavaScript):
1. In **Project Settings → General**
2. Scroll to **"Your apps"** → Click **Web icon (</>)**
3. Register app name: `roomies-web`
4. Copy the `firebaseConfig` object

---

## 💻 Step 4: Install Firebase SDK

```bash
pip install firebase-admin
```

Add to `requirements.txt`:
```
firebase-admin>=6.0.0
```

---

## ⚙️ Step 5: Configure Firebase in Your App

### A. Update `.env` file
Add these lines:
```env
# Firebase Configuration
FIREBASE_CREDENTIALS_PATH=firebase-credentials.json
FIREBASE_STORAGE_BUCKET=roomies-platform.appspot.com
```

### B. Update `.gitignore`
Add this line to prevent committing credentials:
```
firebase-credentials.json
```

---

## 🔧 Step 6: Create Firebase Utility File

Create a new file: `utils/firebase_storage.py`

```python
import os
import firebase_admin
from firebase_admin import credentials, storage
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

load_dotenv()

# Initialize Firebase Admin SDK
def init_firebase():
    """Initialize Firebase Admin SDK."""
    cred_path = os.getenv('FIREBASE_CREDENTIALS_PATH')
    
    if not cred_path or not os.path.exists(cred_path):
        print("⚠️ Firebase credentials not found. Storage features disabled.")
        return False
    
    if not firebase_admin._apps:
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred, {
            'storageBucket': os.getenv('FIREBASE_STORAGE_BUCKET')
        })
        print("✅ Firebase initialized successfully")
    
    return True


def upload_file_to_firebase(file, folder='uploads'):
    """
    Upload a file to Firebase Storage.
    
    Args:
        file: Werkzeug FileStorage object
        folder: Folder name in Firebase Storage
    
    Returns:
        Public URL of uploaded file or None
    """
    if not init_firebase():
        return None
    
    try:
        filename = secure_filename(file.filename)
        bucket = storage.bucket()
        
        # Create blob path
        blob = bucket.blob(f'{folder}/{filename}')
        
        # Upload file
        blob.upload_from_string(
            file.read(),
            content_type=file.content_type
        )
        
        # Make public
        blob.make_public()
        
        return blob.public_url
    
    except Exception as e:
        print(f"Firebase upload error: {e}")
        return None


def delete_file_from_firebase(file_url):
    """Delete a file from Firebase Storage by URL."""
    if not init_firebase():
        return False
    
    try:
        bucket = storage.bucket()
        # Extract blob name from URL
        blob_name = file_url.split(f"{bucket.name}/")[-1]
        blob = bucket.blob(blob_name)
        blob.delete()
        return True
    except Exception as e:
        print(f"Firebase delete error: {e}")
        return False
```

---

## 🖼️ Step 7: Use Firebase in Your Routes

### Example: Upload Room Image

```python
from utils.firebase_storage import upload_file_to_firebase

@app.route('/api/upload-room-image', methods=['POST'])
@login_required
def upload_room_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400
    
    file = request.files['image']
    
    # Upload to Firebase
    image_url = upload_file_to_firebase(file, folder='room-images')
    
    if image_url:
        return jsonify({'success': True, 'url': image_url})
    else:
        return jsonify({'error': 'Upload failed'}), 500
```

---

## 🌐 Step 8: Frontend Integration (Optional)

Add to your HTML templates:

```html
<!-- Firebase SDK -->
<script src="https://www.gstatic.com/firebasejs/10.7.0/firebase-app-compat.js"></script>
<script src="https://www.gstatic.com/firebasejs/10.7.0/firebase-storage-compat.js"></script>

<script>
// Your Firebase Config (from Step 3)
const firebaseConfig = {
    apiKey: "YOUR_API_KEY",
    authDomain: "roomies-platform.firebaseapp.com",
    projectId: "roomies-platform",
    storageBucket: "roomies-platform.appspot.com",
    messagingSenderId: "YOUR_SENDER_ID",
    appId: "YOUR_APP_ID"
};

firebase.initializeApp(firebaseConfig);
</script>
```

---

## 📊 Step 9: Firebase Free Tier Limits

✅ **What You Get FREE:**
- **Storage**: 5 GB
- **Downloads**: 1 GB/day
- **Firestore**: 1 GB storage, 50K reads/day, 20K writes/day
- **Authentication**: Unlimited users
- **Hosting**: 10 GB bandwidth/month

---

## 🔒 Step 10: Security Best Practices

### A. Environment Variables
Store all config in `.env`:
```env
FIREBASE_API_KEY=your_api_key
FIREBASE_AUTH_DOMAIN=roomies-platform.firebaseapp.com
FIREBASE_PROJECT_ID=roomies-platform
FIREBASE_STORAGE_BUCKET=roomies-platform.appspot.com
FIREBASE_MESSAGING_SENDER_ID=your_sender_id
FIREBASE_APP_ID=your_app_id
```

### B. Before Pushing to GitHub
1. Create `.env.example` with dummy values:
```env
FIREBASE_CREDENTIALS_PATH=firebase-credentials.json
FIREBASE_STORAGE_BUCKET=your-project.appspot.com
```

2. Ensure `.gitignore` includes:
```
.env
firebase-credentials.json
*.json
!package.json
```

3. Add README note:
```markdown
## Firebase Setup
1. Copy `.env.example` to `.env`
2. Add your Firebase credentials
3. Download service account JSON from Firebase Console
```

---

## 🚀 Step 11: Test Firebase Integration

Run this test script:

```python
# test_firebase.py
from utils.firebase_storage import init_firebase, upload_file_to_firebase

if __name__ == "__main__":
    if init_firebase():
        print("✅ Firebase is configured correctly!")
    else:
        print("❌ Firebase setup incomplete")
```

---

## 📝 Summary

You now have:
- ✅ Firebase Storage for images
- ✅ Secure credential management
- ✅ GitHub-ready configuration
- ✅ Free tier optimization

**Next Steps:**
1. Complete the Firebase Console setup
2. Download credentials
3. Run the integration code
4. Test with actual file uploads
5. Push to GitHub (credentials excluded)

Need help with any specific Firebase feature? Let me know!
