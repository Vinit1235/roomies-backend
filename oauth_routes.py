"""
Google OAuth Routes for Roomies
Add these routes to app.py after the existing authentication routes
"""

# Import at the top of app.py (add to existing imports)
try:
    from utils.google_oauth import (
        get_google_auth_url,
        authenticate_google_user,
        is_google_oauth_available
    )
    GOOGLE_OAUTH_ENABLED = is_google_oauth_available()
    if GOOGLE_OAUTH_ENABLED:
        print("✅ Google OAuth enabled")
    else:
        print("⚠️ Google OAuth not configured (missing credentials)")
except ImportError as e:
    print(f"⚠️ Could not import google_oauth: {e}. Google OAuth disabled.")
    GOOGLE_OAUTH_ENABLED = False
    def get_google_auth_url(role="student"):
        return False, "Google OAuth not available"
    def authenticate_google_user(code):
        return False, {"error": "Google OAuth not available"}


# ============= GOOGLE OAUTH ROUTES =============
# Add these routes to app.py (after line ~1070, before the existing routes)

@app.route("/auth/google")
def google_oauth_login():
    """Initiate Google OAuth flow."""
    role = request.args.get("role", "student")
    
    if role not in ["student", "owner"]:
        flash("Invalid role selected.", "error")
        return redirect(url_for("home"))
    
    success, auth_url = get_google_auth_url(role)
    
    if success:
        return redirect(auth_url)
    else:
        flash(f"OAuth error: {auth_url}", "error")
        return redirect(url_for("home"))


@app.route("/auth/google/callback")
def google_oauth_callback():
    """Handle Google OAuth callback."""
    # Get authorization code
    code = request.args.get("code")
    state = request.args.get("state")
    error = request.args.get("error")
    
    # Handle OAuth errors
    if error:
        flash(f"OAuth error: {error}", "error")
        return redirect(url_for("home"))
    
    if not code:
        flash("No authorization code received.", "error")
        return redirect(url_for("home"))
    
    # Extract role from state
    role = "student"  # default
    if state and ":" in state:
        role = state.split(":")[0]
    
    # Authenticate with Google
    success, user_data = authenticate_google_user(code)
    
    if not success:
        error_msg = user_data.get("error", "Authentication failed")
        flash(f"Google login failed: {error_msg}", "error")
        return redirect(url_for("home"))
    
    # Extract user information
    email = user_data.get("email")
    name = user_data.get("name")
    google_id = user_data.get("google_id")
    email_verified = user_data.get("email_verified", False)
    
    if not email:
        flash("Could not retrieve email from Google.", "error")
        return redirect(url_for("home"))
    
    # Create or update user in database
    try:
        if role == "student":
            # Check if student exists
            student = Student.query.filter_by(email=email).first()
            
            if not student:
                # Create new student
                student = Student(
                    email=email,
                    name=name or email.split("@")[0],
                    college="Unknown",  # User can update later
                    verified=email_verified,
                    role="student"
                )
                # Set random password (OAuth users don't need it)
                student.set_password(secrets.token_urlsafe(32))
                db.session.add(student)
                db.session.commit()
                
                # Create wallet for new student
                wallet = Wallet(student_id=student.id, balance=0.0)
                db.session.add(wallet)
                db.session.commit()
                
                flash(f"Welcome to Roomies, {name}! Please complete your profile.", "success")
            else:
                # Update existing student
                if not student.verified and email_verified:
                    student.verified = True
                    db.session.commit()
                flash(f"Welcome back, {student.name}!", "success")
            
            # Log in the student
            login_user(student, remember=True)
            return redirect(url_for("explore"))
            
        elif role == "owner":
            # Check if owner exists
            owner = Owner.query.filter_by(email=email).first()
            
            if not owner:
                # Create new owner
                owner = Owner(
                    email=email,
                    name=name or email.split("@")[0],
                    kyc_verified=False  # Owner needs to complete KYC
                )
                # Set random password (OAuth users don't need it)
                owner.set_password(secrets.token_urlsafe(32))
                db.session.add(owner)
                db.session.commit()
                
                flash(f"Welcome to Roomies, {name}! Please complete your KYC verification.", "success")
            else:
                flash(f"Welcome back, {owner.name}!", "success")
            
            # Log in the owner
            login_user(owner, remember=True)
            return redirect(url_for("list_room"))
        
        else:
            flash("Invalid role.", "error")
            return redirect(url_for("home"))
            
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"OAuth user creation failed: {e}")
        flash("Failed to create user account. Please try again.", "error")
        return redirect(url_for("home"))


@app.route("/auth/github")
def github_oauth_login():
    """Initiate GitHub OAuth flow via Supabase."""
    role = request.args.get("role", "student")
    
    if role not in ["student", "owner"]:
        flash("Invalid role selected.", "error")
        return redirect(url_for("home"))
    
    # Use Supabase OAuth for GitHub
    if not OAUTH_ENABLED:
        flash("GitHub OAuth is not configured.", "error")
        return redirect(url_for("home"))
    
    success, auth_url = get_github_oauth_url(redirect_to=f"/auth/callback?role={role}")
    
    if success:
        return redirect(auth_url)
    else:
        flash(f"OAuth error: {auth_url}", "error")
        return redirect(url_for("home"))


@app.route("/auth/callback")
def oauth_callback():
    """Handle Supabase OAuth callback (for GitHub and Supabase Google)."""
    code = request.args.get("code")
    access_token = request.args.get("access_token")
    role = request.args.get("role", "student")
    error = request.args.get("error")
    
    if error:
        flash(f"OAuth error: {error}", "error")
        return redirect(url_for("home"))
    
    if not code and not access_token:
        flash("No authorization code received.", "error")
        return redirect(url_for("home"))
    
    # Handle OAuth callback via Supabase
    success, user_data = handle_oauth_callback(code=code, access_token=access_token)
    
    if not success:
        error_msg = user_data.get("error", "Authentication failed")
        flash(f"Login failed: {error_msg}", "error")
        return redirect(url_for("home"))
    
    # Extract user information
    email = user_data.get("email")
    name = user_data.get("name")
    email_verified = user_data.get("email_verified", False)
    
    if not email:
        flash("Could not retrieve email from OAuth provider.", "error")
        return redirect(url_for("home"))
    
    # Create or update user (same logic as Google OAuth)
    try:
        if role == "student":
            student = Student.query.filter_by(email=email).first()
            
            if not student:
                student = Student(
                    email=email,
                    name=name or email.split("@")[0],
                    college="Unknown",
                    verified=email_verified,
                    role="student"
                )
                student.set_password(secrets.token_urlsafe(32))
                db.session.add(student)
                db.session.commit()
                
                wallet = Wallet(student_id=student.id, balance=0.0)
                db.session.add(wallet)
                db.session.commit()
                
                flash(f"Welcome to Roomies, {name}!", "success")
            else:
                if not student.verified and email_verified:
                    student.verified = True
                    db.session.commit()
                flash(f"Welcome back, {student.name}!", "success")
            
            login_user(student, remember=True)
            return redirect(url_for("explore"))
            
        elif role == "owner":
            owner = Owner.query.filter_by(email=email).first()
            
            if not owner:
                owner = Owner(
                    email=email,
                    name=name or email.split("@")[0],
                    kyc_verified=False
                )
                owner.set_password(secrets.token_urlsafe(32))
                db.session.add(owner)
                db.session.commit()
                
                flash(f"Welcome to Roomies, {name}!", "success")
            else:
                flash(f"Welcome back, {owner.name}!", "success")
            
            login_user(owner, remember=True)
            return redirect(url_for("list_room"))
        
        else:
            flash("Invalid role.", "error")
            return redirect(url_for("home"))
            
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"OAuth user creation failed: {e}")
        flash("Failed to create user account. Please try again.", "error")
        return redirect(url_for("home"))
