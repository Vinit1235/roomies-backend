# Verification Feature - Role-Based Updates

## What Changed

### For Students:
**Required Documents:**
- ✅ Student ID Card (required)
- ✅ Government ID - Aadhaar/PAN/Passport (required)
- ✅ College Letter/Bonafide (optional)

### For Owners:
**Required Documents:**
- ✅ Government ID - Aadhaar/PAN/Passport (required)
- ✅ Electricity Bill (required) - NEW!

## Technical Changes

### 1. Database Schema
Added new column to `verifications` table:
- `electricity_bill_path` VARCHAR(512) - Stores path to electricity bill upload

### 2. Frontend Updates (`verify_upload.html`)
- Student ID and College Letter fields now only show for students
- Electricity Bill upload field now shows for owners
- Updated JavaScript validation to check user role
- Role-based form validation (different requirements for students vs owners)

### 3. Backend Updates (`app.py`)
- Updated `Verification` model with `electricity_bill_path` column
- Modified `/api/verification/upload` endpoint to:
  - Validate student requirements: Student ID + Government ID
  - Validate owner requirements: Government ID + Electricity Bill
  - Save electricity bill uploads for owners
- Updated admin verification route to include electricity bill in enriched data

### 4. Admin Dashboard (`admin_verifications.html`)
- Added electricity bill preview link
- Shows "Electricity Bill" document for owner verifications

### 5. Migration Script
- Updated `migrations/add_verifications.py` to add electricity_bill_path column
- Migration successfully applied to database

## Testing

### As Student:
1. Login as student
2. Go to `/verify`
3. Should see:
   - Student ID Card upload (required)
   - College Letter upload (optional)
   - Government ID upload (required)
4. Upload documents and submit

### As Owner:
1. Signup/Login as owner
2. Go to `/verify`
3. Should see:
   - Government ID upload (required)
   - Electricity Bill upload (required)
4. Upload documents and submit

### As Admin:
1. Login to `/admin/login`
2. Go to `/admin/verifications`
3. View verification requests
4. Click on document links to preview uploads
5. For students: See Student ID, College Letter, Gov ID
6. For owners: See Gov ID, Electricity Bill

## File Changes

### Modified Files:
- `app.py` - Added electricity_bill_path to model and routes
- `templates/verify_upload.html` - Role-based field display and validation
- `templates/admin_verifications.html` - Added electricity bill display
- `migrations/add_verifications.py` - Column migration script

### Database:
- ✅ `electricity_bill_path` column added to `verifications` table

## Requirements by Role

| Document Type | Students | Owners |
|--------------|----------|--------|
| Student ID Card | ✅ Required | ❌ Not shown |
| College Letter | ⚪ Optional | ❌ Not shown |
| Government ID | ✅ Required | ✅ Required |
| Electricity Bill | ❌ Not shown | ✅ Required |

## Status
✅ **COMPLETE AND TESTED**
- Database migrated successfully
- App running without errors
- Role-based validation working
- File uploads configured correctly
