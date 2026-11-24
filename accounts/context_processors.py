def auth_user_context(request):
    """
    Supplies authentication and system context to all templates.
    """
    user = getattr(request, 'mongo_user', None)
    if user:
        return {
            'current_user': user,
            'is_authenticated': True,
            'user_role': user.get('role', 'Public User'),
            'is_admin': user.get('role') == 'Administrator',
            'is_authority': user.get('role') in ['Administrator', 'Traffic Authority'],
            'is_public': user.get('role') == 'Public User',
            'app_title': 'AI Smart Traffic Analyzer',
            'system_theme': 'purple',
        }
    return {
        'current_user': None,
        'is_authenticated': False,
        'user_role': 'Guest',
        'is_admin': False,
        'is_authority': False,
        'is_public': True,
        'app_title': 'AI Smart Traffic Analyzer',
        'system_theme': 'purple',
    }
