"""Firebase Storage utility for uploading images and files."""
import os
import firebase_admin
from firebase_admin import credentials, storage
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

_firebase_initialized = False


def init_firebase():
    """Initialize Firebase Admin SDK."""
    global _firebase_initialized
    
    if _firebase_initialized:
        return True
    
    cred_path = os.getenv('FIREBASE_CREDENTIALS_PATH')
    
    if not cred_path or not os.path.exists(cred_path):
        print("⚠️ Firebase credentials not found. Storage features disabled.")
        return False
    
    try:
        if not firebase_admin._apps:
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred, {
                'storageBucket': os.getenv('FIREBASE_STORAGE_BUCKET')
            })
            print("✅ Firebase initialized successfully")
            _firebase_initialized = True
        return True
    except Exception as e:
        print(f"❌ Firebase initialization error: {e}")
        return False


def upload_file_to_firebase(file, folder='uploads', custom_filename=None):
    """
    Upload a file to Firebase Storage.
    
    Args:
        file: Werkzeug FileStorage object
        folder: Folder name in Firebase Storage
        custom_filename: Optional custom filename (will be sanitized)
    
    Returns:
        Public URL of uploaded file or None
    """
    if not init_firebase():
        return None
    
    try:
        # Generate filename
        if custom_filename:
            filename = secure_filename(custom_filename)
        else:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            original_filename = secure_filename(file.filename)
            filename = f"{timestamp}_{original_filename}"
        
        bucket = storage.bucket()
        
        # Create blob path
        blob_path = f'{folder}/{filename}'
        blob = bucket.blob(blob_path)
        
        # Upload file
        blob.upload_from_string(
            file.read(),
            content_type=file.content_type or 'application/octet-stream'
        )
        
        # Make public
        blob.make_public()
        
        print(f"✅ File uploaded to Firebase: {blob.public_url}")
        return blob.public_url
    
    except Exception as e:
        print(f"❌ Firebase upload error: {e}")
        return None


def upload_bytes_to_firebase(file_bytes, filename, folder='uploads', content_type='image/jpeg'):
    """
    Upload raw bytes to Firebase Storage.
    
    Args:
        file_bytes: Raw file bytes
        filename: Name for the file
        folder: Folder name in Firebase Storage
        content_type: MIME type of the file
    
    Returns:
        Public URL of uploaded file or None
    """
    if not init_firebase():
        return None
    
    try:
        filename = secure_filename(filename)
        bucket = storage.bucket()
        
        blob_path = f'{folder}/{filename}'
        blob = bucket.blob(blob_path)
        
        blob.upload_from_string(
            file_bytes,
            content_type=content_type
        )
        
        blob.make_public()
        
        print(f"✅ Bytes uploaded to Firebase: {blob.public_url}")
        return blob.public_url
    
    except Exception as e:
        print(f"❌ Firebase upload error: {e}")
        return None


def delete_file_from_firebase(file_url):
    """
    Delete a file from Firebase Storage by URL.
    
    Args:
        file_url: Full public URL of the file
    
    Returns:
        True if deleted successfully, False otherwise
    """
    if not init_firebase():
        return False
    
    try:
        bucket = storage.bucket()
        bucket_name = bucket.name
        
        # Extract blob name from URL
        if bucket_name in file_url:
            blob_name = file_url.split(f"{bucket_name}/")[-1].split("?")[0]
            blob = bucket.blob(blob_name)
            blob.delete()
            print(f"✅ File deleted from Firebase: {blob_name}")
            return True
        else:
            print(f"❌ Invalid Firebase URL: {file_url}")
            return False
    
    except Exception as e:
        print(f"❌ Firebase delete error: {e}")
        return False


def list_files_in_folder(folder='uploads'):
    """
    List all files in a Firebase Storage folder.
    
    Args:
        folder: Folder name
    
    Returns:
        List of file URLs or empty list
    """
    if not init_firebase():
        return []
    
    try:
        bucket = storage.bucket()
        blobs = bucket.list_blobs(prefix=folder)
        
        urls = []
        for blob in blobs:
            blob.make_public()
            urls.append(blob.public_url)
        
        return urls
    
    except Exception as e:
        print(f"❌ Firebase list error: {e}")
        return []
