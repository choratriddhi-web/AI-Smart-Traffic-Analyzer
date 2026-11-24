import bcrypt
from datetime import datetime
from bson import ObjectId
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from services.mongodb import get_collection
from accounts.decorators import mongo_login_required, role_required

def login_view(request):
    """
    Renders login form and processes authentication for Traffic Authority Control Room.
    """
    prefill_user = request.GET.get('user', '')
    next_url = request.GET.get('next', '')

    if getattr(request, 'mongo_user', None):
        user_role = request.mongo_user.get('role')
        if user_role == 'Traffic Authority':
            return redirect('dashboard:index')
        return redirect('public:dashboard')

    if request.method == 'POST':
        login_id = request.POST.get('login_id', '').strip()
        password = request.POST.get('password', '').strip()

        if not login_id or not password:
            messages.error(request, "Please enter both officer username/email and password.")
            return render(request, 'accounts/login.html', {'prefill_user': login_id})

        users_col = get_collection('users')
        user = users_col.find_one({
            "$or": [{"username": login_id}, {"email": login_id.lower()}]
        })

        if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
            if not user.get('is_active', True):
                messages.error(request, "This account is disabled. Contact your traffic department supervisor.")
                return render(request, 'accounts/login.html', {'prefill_user': login_id})

            request.session['user_id'] = str(user['_id'])
            
            if user.get('role') == 'Traffic Authority':
                messages.success(request, f"Welcome to Traffic Command Center, Officer {user.get('full_name', user['username'])}!")
                return redirect(next_url or 'dashboard:index')
            else:
                messages.success(request, f"Welcome to Public Citizen Portal, {user.get('full_name', user['username'])}!")
                return redirect(next_url or 'public:dashboard')
        else:
            messages.error(request, "Invalid credentials. Please verify your officer username/email and password.")

    return render(request, 'accounts/login.html', {'prefill_user': prefill_user})

def citizen_login_view(request):
    """
    Renders login form and processes authentication for Public Citizen Portal.
    Allows citizens to sign in with their registered citizen account.
    """
    prefill_user = request.GET.get('user', '')
    next_url = request.GET.get('next', '')

    if getattr(request, 'mongo_user', None):
        user_role = request.mongo_user.get('role')
        if user_role == 'Public User':
            return redirect('public:dashboard')
        return redirect('dashboard:index')

    if request.method == 'POST':
        login_id = request.POST.get('login_id', '').strip()
        password = request.POST.get('password', '').strip()

        if not login_id or not password:
            messages.error(request, "Please enter your citizen username/email and password.")
            return render(request, 'accounts/citizen_login.html', {'prefill_user': login_id})

        users_col = get_collection('users')
        user = users_col.find_one({
            "$or": [{"username": login_id}, {"email": login_id.lower()}]
        })

        if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
            if not user.get('is_active', True):
                messages.error(request, "This citizen account is deactivated. Contact city traffic support.")
                return render(request, 'accounts/citizen_login.html', {'prefill_user': login_id})

            request.session['user_id'] = str(user['_id'])
            messages.success(request, f"Welcome to Public Citizen Portal, {user.get('full_name', user['username'])}!")
            
            if user.get('role') == 'Traffic Authority':
                return redirect(next_url or 'dashboard:index')
            return redirect(next_url or 'public:dashboard')
        else:
            messages.error(request, "Invalid credentials. Please check your username/email and password.")

    return render(request, 'accounts/citizen_login.html', {'prefill_user': prefill_user})

def citizen_register_view(request):
    """
    Registers a new Public Citizen commuter with their contact and residential details.
    After registration, strictly redirects to the citizen login screen for explicit authentication.
    """
    if getattr(request, 'mongo_user', None):
        user_role = request.mongo_user.get('role')
        if user_role == 'Public User':
            return redirect('public:dashboard')
        return redirect('dashboard:index')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip().lower()
        full_name = request.POST.get('full_name', '').strip()
        phone = request.POST.get('phone', '').strip()
        city = request.POST.get('city', '').strip()
        password = request.POST.get('password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()

        if not username or not email or not password:
            messages.error(request, "Please fill in all mandatory fields (Username, Email, Password).")
            return render(request, 'accounts/citizen_register.html')

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, 'accounts/citizen_register.html')

        if len(password) < 6:
            messages.error(request, "Password must be at least 6 characters.")
            return render(request, 'accounts/citizen_register.html')

        users_col = get_collection('users')
        if users_col.find_one({"$or": [{"username": username}, {"email": email}]}):
            messages.error(request, "A citizen account with that username or email already exists.")
            return render(request, 'accounts/citizen_register.html')

        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

        new_user = {
            "username": username,
            "email": email,
            "password": hashed,
            "full_name": full_name or username,
            "phone": phone or "+91 98000 00000",
            "city": city or "City Center",
            "role": "Public User",
            "created_at": datetime.utcnow(),
            "is_active": True
        }
        users_col.insert_one(new_user)

        # Do NOT auto-login. Redirect user to Citizen Login screen with success notification.
        messages.success(request, f"Citizen account registered successfully for {username}! Please sign in below to enter the portal.")
        return redirect(f"/auth/citizen/login/?user={username}&registered=true")

    return render(request, 'accounts/citizen_register.html')

def register_view(request):
    """
    Registers a new Traffic Authority Officer with complete departmental information.
    After registration, strictly redirects to the login screen for explicit authentication.
    """
    if getattr(request, 'mongo_user', None):
        user_role = request.mongo_user.get('role')
        if user_role == 'Traffic Authority':
            return redirect('dashboard:index')
        return redirect('public:dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip().lower()
        full_name = request.POST.get('full_name', '').strip()
        phone = request.POST.get('phone', '').strip()
        department = request.POST.get('department', '').strip()
        badge_id = request.POST.get('badge_id', '').strip()
        password = request.POST.get('password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()

        if not username or not email or not password:
            messages.error(request, "Please fill in all mandatory fields.")
            return render(request, 'accounts/register.html')

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, 'accounts/register.html')

        if len(password) < 6:
            messages.error(request, "Password must be at least 6 characters.")
            return render(request, 'accounts/register.html')

        users_col = get_collection('users')
        if users_col.find_one({"$or": [{"username": username}, {"email": email}]}):
            messages.error(request, "An officer with that username or email already exists.")
            return render(request, 'accounts/register.html')

        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

        new_user = {
            "username": username,
            "email": email,
            "password": hashed,
            "full_name": full_name or username,
            "phone": phone,
            "department": department or "Traffic Management Branch",
            "badge_id": badge_id or "TP-REG",
            "role": "Traffic Authority",
            "created_at": datetime.utcnow(),
            "is_active": True
        }
        users_col.insert_one(new_user)

        # Do NOT auto-login. Redirect user to the login screen with success notification.
        messages.success(request, f"Officer registration successful for {username}! Please sign in below to enter the Command Center.")
        return redirect(f"/auth/login/?user={username}&registered=true")

    return render(request, 'accounts/register.html')

def logout_view(request):
    """
    Clears the session and redirects to gateway.
    """
    request.session.flush()
    messages.info(request, "You have been logged out successfully.")
    return redirect('gateway')

@mongo_login_required
def profile_view(request):
    """
    Displays and updates user profile information.
    """
    user = request.mongo_user
    users_col = get_collection('users')

    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        phone = request.POST.get('phone', '').strip()
        new_password = request.POST.get('new_password', '').strip()

        update_fields = {
            "full_name": full_name,
            "phone": phone,
            "updated_at": datetime.utcnow()
        }

        if new_password:
            if len(new_password) < 6:
                messages.error(request, "Password must be at least 6 characters long.")
                return render(request, 'accounts/profile.html', {'user': user})
            salt = bcrypt.gensalt()
            update_fields["password"] = bcrypt.hashpw(new_password.encode('utf-8'), salt).decode('utf-8')

        users_col.update_one({"_id": ObjectId(user['id'])}, {"$set": update_fields})
        messages.success(request, "Profile updated successfully.")
        return redirect('accounts:profile')

    return render(request, 'accounts/profile.html', {'user': user})

@mongo_login_required
@role_required(['Traffic Authority'])
def user_management_view(request):
    """
    Traffic Authority panel to review user accounts.
    """
    users_col = get_collection('users')
    all_users = list(users_col.find().sort("created_at", -1))
    for u in all_users:
        u['id'] = str(u['_id'])
    return render(request, 'users/index.html', {'users': all_users})

@mongo_login_required
@role_required(['Traffic Authority'])
def update_user_role(request, user_id):
    """
    Traffic Authority action to toggle active state or switch between the 2 roles.
    """
    if request.method == 'POST':
        new_role = request.POST.get('role')
        is_active = request.POST.get('is_active') == 'true'
        users_col = get_collection('users')
        if new_role in ['Traffic Authority', 'Public User']:
            users_col.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"role": new_role, "is_active": is_active, "updated_at": datetime.utcnow()}}
            )
            messages.success(request, f"User permissions updated successfully.")
        return redirect('accounts:users')
    return redirect('accounts:users')
