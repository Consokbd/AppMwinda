"""
Debug views to diagnose setup issues on Render.
"""
from django.shortcuts import render
from django.contrib.auth import get_user_model
from django.db import connection

User = get_user_model()


def debug_status(request):
    """Show database and auth status."""
    
    # Get all users
    all_users = list(User.objects.all().values('username', 'email', 'is_superuser', 'is_staff', 'role'))
    
    # Check if admin exists
    admin_users = list(User.objects.filter(is_superuser=True).values('username', 'email'))
    
    # Get database info
    db_info = {
        'engine': connection.settings_dict.get('ENGINE', 'unknown'),
        'name': connection.settings_dict.get('NAME', 'unknown'),
    }
    
    # Test AUTH_USER_MODEL
    from django.conf import settings
    auth_user_model = settings.AUTH_USER_MODEL
    
    context = {
        'all_users': all_users,
        'admin_users': admin_users,
        'admin_count': len(admin_users),
        'total_user_count': len(all_users),
        'db_info': db_info,
        'auth_user_model': auth_user_model,
        'user_table_exists': 'users_user' in connection.introspection.table_names(),
    }
    
    return render(request, 'debug_status.html', context)
