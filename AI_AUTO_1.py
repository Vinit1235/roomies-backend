# ============================================
# Flask + n8n Integration for Roomies Platform
# ============================================

from flask import Flask, request, jsonify, session
from werkzeug.utils import secure_filename
import requests
import os
import base64
from datetime import datetime

app = Flask(__name__)

# ============================================
# CONFIGURATION
# ============================================

# n8n webhook URL
# For TESTING in n8n (when you click "Execute Node" or "Listen"): use /webhook-test/
# For PRODUCTION (when the workflow is active): use /webhook/
# Make sure the path matches what you set in n8n
N8N_WEBHOOK_URL = "http://localhost:5678/webhook-test/verified"

# File upload settings
UPLOAD_FOLDER = 'uploads/documents'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ============================================
# HELPER FUNCTIONS
# ============================================

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_url(filename):
    """
    Generate URL for uploaded file
    In production, this would be your cloud storage URL (S3, Cloudinary, etc.)
    For local testing, we'll serve it from Flask
    """
    return f"http://127.0.0.1:5001/uploads/documents/{filename}"

# ============================================
# ROUTE 1: Serve Uploaded Files (for local testing)
# ============================================

@app.route('/uploads/documents/<filename>')
def serve_document(filename):
    """Serve uploaded documents - Only for local testing"""
    from flask import send_from_directory
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# ============================================
# ROUTE 2: Upload Document (Student Upload Form)
# ============================================

@app.route('/api/upload-document', methods=['POST'])
def upload_document():
    """
    Handle document upload from frontend
    
    Form data expected:
    - file: The document image/PDF
    - user_id: Student's user ID
    - user_name: Student's full name
    - email: Student's email
    """
    
    # Check if file is present
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Only PNG, JPG, JPEG, PDF allowed'}), 400
    
    # Get user data from form
    user_id = request.form.get('user_id')
    user_name = request.form.get('user_name')
    email = request.form.get('email')
    
    if not all([user_id, user_name, email]):
        return jsonify({'error': 'Missing user information'}), 400
    
    # Save file with secure filename
    filename = secure_filename(file.filename)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    unique_filename = f"{user_id}_{timestamp}_{filename}"
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
    file.save(file_path)
    
    # Generate file URL
    document_url = get_file_url(unique_filename)
    
    # Generate Base64 for AI (since localhost URLs won't work for OpenAI)
    # OpenAI cannot access "http://127.0.0.1...", so we send the actual image data
    try:
        with open(file_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            
        # Determine mime type
        mime_type = 'image/jpeg'
        if filename.lower().endswith('.png'): mime_type = 'image/png'
        elif filename.lower().endswith('.pdf'): mime_type = 'application/pdf'
        
        document_base64 = f"data:{mime_type};base64,{encoded_string}"
    except Exception as e:
        print(f"⚠️ Error encoding file to base64: {e}")
        document_base64 = None

    # Update user status to "pending verification" in your database
    # Example:
    # user = User.query.get(user_id)
    # user.verification_status = 'pending'
    # user.document_url = document_url
    # db.session.commit()
    
    print(f"✅ Document uploaded: {unique_filename}")
    print(f"📄 Document URL: {document_url}")
    
    # NOW TRIGGER N8N WEBHOOK FOR VERIFICATION
    try:
        webhook_data = {
            'user_id': user_id,
            'user_name': user_name,
            'document_url': document_url,
            'document_base64': document_base64, # Use this in n8n OpenAI node
            'email': email
        }
        
        print(f"🚀 Triggering n8n webhook...")
        response = requests.post(
            N8N_WEBHOOK_URL,
            json=webhook_data,
            timeout=60
        )
        
        print(f"✅ n8n webhook triggered. Status: {response.status_code}")
        if response.status_code != 200:
            print(f"⚠️ n8n Response: {response.text}")
        
        return jsonify({
            'status': 'success',
            'message': 'Document uploaded and verification initiated',
            'document_url': document_url,
            'filename': unique_filename,
            'verification_status': 'pending'
        }), 200
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error triggering n8n: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Document uploaded but verification failed to start',
            'error': str(e)
        }), 500

# ============================================
# ROUTE 3: Receive Verification Result from n8n
# ============================================

@app.route('/api/update-verification-status', methods=['POST'])
def update_verification_status():
    """
    This endpoint is called by n8n workflow after AI verification
    
    Expected JSON from n8n:
    {
        "user_id": "123",
        "status": "verified" or "rejected",
        "confidence": 85,
        "extracted_name": "John Doe"
    }
    """
    
    try:
        data = request.json
        print(f"📨 Received verification result from n8n: {data}")
        
        user_id = data.get('user_id')
        status = data.get('status')  # 'verified' or 'rejected'
        confidence = data.get('confidence')
        extracted_name = data.get('extracted_name')
        
        # Update database
        # Example with SQLAlchemy:
        # user = User.query.get(user_id)
        # if user:
        #     user.verification_status = status
        #     user.verification_confidence = confidence
        #     user.verified_name = extracted_name
        #     user.verified_at = datetime.utcnow()
        #     db.session.commit()
        
        # For now, just print (you'll replace this with your DB code)
        print(f"✅ User {user_id} verification status updated to: {status}")
        print(f"   Confidence: {confidence}%")
        print(f"   Extracted Name: {extracted_name}")
        
        return jsonify({
            'status': 'success',
            'message': 'Verification status updated',
            'user_id': user_id,
            'verification_status': status
        }), 200
        
    except Exception as e:
        print(f"❌ Error updating verification status: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# ============================================
# ROUTE 4: Check Verification Status (for Frontend)
# ============================================

@app.route('/api/verification-status/<user_id>', methods=['GET'])
def get_verification_status(user_id):
    """
    Frontend can poll this to check verification status
    """
    
    # Get from database
    # user = User.query.get(user_id)
    # if not user:
    #     return jsonify({'error': 'User not found'}), 404
    
    # For demo, return sample response
    return jsonify({
        'user_id': user_id,
        'verification_status': 'pending',  # or 'verified' or 'rejected'
        'confidence': None,
        'verified_at': None
    }), 200

# ============================================
# ROUTE 5: Manual Trigger (for Testing)
# ============================================

@app.route('/api/test-verification', methods=['POST'])
def test_verification():
    """
    Test endpoint to trigger verification with sample data
    Useful for testing without uploading real documents
    """
    
    test_data = {
        'user_id': 'test_123',
        'user_name': 'John Doe',
        'document_url': 'https://upload.wikimedia.org/wikipedia/commons/8/8d/ID_card_icon.svg',
        'email': request.json.get('email', 'test@example.com')
    }
    
    try:
        response = requests.post(N8N_WEBHOOK_URL, json=test_data, timeout=30)
        
        return jsonify({
            'status': 'success',
            'message': 'Test verification triggered',
            'n8n_status': response.status_code
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# ============================================
# HTML FORM FOR TESTING (Optional)
# ============================================

@app.route('/verify-test')
def verify_test_page():
    """Simple HTML form to test document upload"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test ID Verification</title>
        <style>
            body { font-family: Arial; max-width: 600px; margin: 50px auto; padding: 20px; }
            input, button { margin: 10px 0; padding: 10px; width: 100%; }
            button { background: #4CAF50; color: white; border: none; cursor: pointer; }
            button:hover { background: #45a049; }
            #status { margin-top: 20px; padding: 10px; border-radius: 5px; }
            .success { background: #d4edda; color: #155724; }
            .error { background: #f8d7da; color: #721c24; }
            .pending { background: #fff3cd; color: #856404; }
        </style>
    </head>
    <body>
        <h1>🔐 Test ID Verification</h1>
        <form id="uploadForm">
            <input type="text" id="user_id" placeholder="User ID" value="test_123" required>
            <input type="text" id="user_name" placeholder="Full Name" value="John Doe" required>
            <input type="email" id="email" placeholder="Email" value="test@example.com" required>
            <input type="file" id="document" accept="image/*,.pdf" required>
            <button type="submit">Upload & Verify</button>
        </form>
        
        <div id="status"></div>
        
        <script>
            document.getElementById('uploadForm').onsubmit = async (e) => {
                e.preventDefault();
                
                const statusDiv = document.getElementById('status');
                statusDiv.innerHTML = '<div class="pending">⏳ Uploading and verifying...</div>';
                
                const formData = new FormData();
                formData.append('file', document.getElementById('document').files[0]);
                formData.append('user_id', document.getElementById('user_id').value);
                formData.append('user_name', document.getElementById('user_name').value);
                formData.append('email', document.getElementById('email').value);
                
                try {
                    const response = await fetch('/api/upload-document', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const result = await response.json();
                    
                    if (response.ok) {
                        statusDiv.innerHTML = `
                            <div class="success">
                                ✅ ${result.message}<br>
                                📄 File: ${result.filename}<br>
                                🔍 Status: ${result.verification_status}<br>
                                <br>Check your email and n8n executions!
                            </div>
                        `;
                    } else {
                        statusDiv.innerHTML = `<div class="error">❌ ${result.error || result.message}</div>`;
                    }
                } catch (error) {
                    statusDiv.innerHTML = `<div class="error">❌ Error: ${error.message}</div>`;
                }
            };
        </script>
    </body>
    </html>
    '''

# ============================================
# RUN THE APP
# ============================================

if __name__ == '__main__':
    print("\n" + "="*50)
    print("🚀 Roomies Flask Server Starting...")
    print("="*50)
    print(f"📍 Server: http://127.0.0.1:5001")
    print(f"🔗 n8n Webhook: {N8N_WEBHOOK_URL}")
    print(f"🧪 Test Page: http://127.0.0.1:5001/verify-test")
    print("="*50 + "\n")
    
    app.run(debug=True, host='127.0.0.1', port=5001)