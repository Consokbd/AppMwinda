"""
Setup initialization for first admin user creation.
Accessible only if no superusers exist.
"""
from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model
from django.views.decorators.http import require_http_methods

User = get_user_model()


def setup_view(request):
    """Initialize admin user if none exists."""
    
    # Check if any superuser exists
    has_admin = User.objects.filter(is_superuser=True).exists()
    
    if has_admin:
        # Redirect to login if admin already exists
        return redirect('login')
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        password_confirm = request.POST.get('password_confirm', '').strip()
        
        errors = []
        
        # Validation
        if not username:
            errors.append('Username is required')
        elif len(username) < 3:
            errors.append('Username must be at least 3 characters')
        elif User.objects.filter(username=username).exists():
            errors.append('Username already exists')
        
        if not email:
            errors.append('Email is required')
        elif '@' not in email:
            errors.append('Invalid email format')
        
        if not password:
            errors.append('Password is required')
        elif len(password) < 6:
            errors.append('Password must be at least 6 characters')
        
        if password != password_confirm:
            errors.append('Passwords do not match')
        
        if not errors:
            # Create admin user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                role='admin',
                direction='design',
            )
            user.is_superuser = True
            user.is_staff = True
            user.save()
            
            return render(request, 'setup_success.html', {
                'username': username,
                'email': email,
            })
        
        context = {
            'errors': errors,
            'form_data': request.POST,
        }
        return render(request, 'setup.html', context)
    
    return render(request, 'setup.html')
