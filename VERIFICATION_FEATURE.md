# User Verification Feature

## Overview
The verification feature allows students and owners to upload documents to verify their identity and gain a "Verified" badge, building trust in the Roomies community.

## Features

### For Users (Students/Owners)
1. **Document Upload Page** (`/verify`)
   - Upload Student ID Card (required)
   - Upload Government ID (Aadhaar/PAN/Passport) (required)
   - Upload College Letter/Bonafide (optional but recommended)
   - Drag & drop or click to upload
   - Max file size: 5MB per document
   - Supported formats: PNG, JPG, PDF

2. **Verification Status**
   - **Pending**: Documents submitted, awaiting admin review (24-48 hours)
   - **Verified**: Account verified with checkmark badge
   - **Rejected**: Documents need resubmission (reason provided)

3. **Access**
   - Sidebar link: "Get Verified" (visible when logged in)
   - Status displayed on verification page

### For Admins
1. **Verification Review Dashboard** (`/admin/verifications`)
   - View all verification requests
   - Filter by status: All, Pending, Verified, Rejected
   - Statistics: Total requests, pending, verified, rejected
   - Preview uploaded documents
   - Approve/Reject actions with reasons

2. **Review Actions**
   - **Approve**: Marks user as verified, updates `verified`/`kyc_verified` status
   - **Reject**: Requires rejection reason, notifies user

## Database Schema

### Verifications Table
```sql
CREATE TABLE verifications (
    id INTEGER PRIMARY KEY,
    user_type VARCHAR(32) NOT NULL,  -- 'student' or 'owner'
    user_id INTEGER NOT NULL,
    student_id_path VARCHAR(512),     -- Path to student ID file
    college_letter_path VARCHAR(512), -- Path to college letter file
    gov_id_path VARCHAR(512),         -- Path to government ID file
    status VARCHAR(32) DEFAULT 'pending',  -- pending, verified, rejected
    rejection_reason TEXT,
    reviewed_by INTEGER REFERENCES admins(id),
    reviewed_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## API Endpoints

### User Endpoints
- `GET /verify` - Verification page (requires login)
- `POST /api/verification/upload` - Upload verification documents

### Admin Endpoints
- `GET /admin/verifications` - View all verification requests (admin only)
- `POST /api/admin/verification/<id>/approve` - Approve verification (admin only)
- `POST /api/admin/verification/<id>/reject` - Reject verification with reason (admin only)

## Setup Instructions

1. **Run Database Migration**
   ```bash
   python migrations/add_verifications.py
   ```
   This creates the `verifications` table and upload directory.

2. **Verify Upload Directory**
   The system automatically creates: `static/uploads/verifications/`
   Files are saved with naming pattern: `{user_type}_{user_id}_{doc_type}_{timestamp}.ext`

3. **Test the Feature**
   - Login as a student/owner
   - Navigate to "Get Verified" in sidebar
   - Upload required documents
   - Login as admin to review: `/admin/verifications`

## File Organization

### Templates
- `templates/verify_upload.html` - User verification page
- `templates/admin_verifications.html` - Admin review dashboard

### Routes (in app.py)
- Lines ~776-895: User verification routes
- Lines ~1300-1450: Admin verification routes

### Models (in app.py)
- Lines ~255-280: Verification model

### Uploads
- `static/uploads/verifications/` - All verification documents stored here

## Security Features

1. **File Validation**
   - Max 5MB per file
   - Allowed formats: image/*, .pdf
   - Unique filenames prevent overwrites

2. **Access Control**
   - Users can only upload for their own account
   - Admin-only access to review dashboard
   - Direct file URLs require authentication

3. **Data Privacy**
   - Files stored securely in uploads directory
   - Only admins can view verification documents
   - Rejection reasons visible only to user and admin

## User Flow

1. User creates account (student/owner)
2. Clicks "Get Verified" in sidebar
3. Uploads required documents:
   - Student ID Card
   - Government ID
   - College Letter (optional)
4. Submits for review
5. Admin reviews within 24-48 hours
6. User receives verified status or rejection reason
7. If rejected, user can resubmit with correct documents

## Admin Workflow

1. Login to admin panel (`/admin/login`)
2. Navigate to "Verification Requests" (`/admin/verifications`)
3. View statistics and pending requests
4. Click on documents to review:
   - Student ID
   - College Letter
   - Government ID
5. Verify identity matches across documents
6. **Approve** if valid OR **Reject** with specific reason
7. User's verified status updates automatically

## Benefits

### For Users
- Build trust and credibility
- Verified badge on profile
- Higher response rates from listings
- Access to premium features (future)

### For Platform
- Reduces fraud and fake accounts
- Increases user trust
- Better quality listings
- Compliance with regulations

## Future Enhancements

1. Email notifications for status changes
2. Auto-verification using OCR/AI
3. Verification expiry (annual renewal)
4. Different verification levels (Basic, Premium)
5. ID verification through video call
6. Integration with DigiLocker (India)

## Troubleshooting

### "Upload failed"
- Check file size (must be < 5MB)
- Ensure correct file format (PNG, JPG, PDF)
- Verify internet connection

### "Verification not found"
- Ensure you're logged in
- Check if documents were submitted
- Contact admin if issue persists

### Admin can't approve/reject
- Verify admin permissions
- Check database connection
- Review server logs for errors

## Support

For issues or questions:
- Check application logs
- Review this documentation
- Contact technical support
