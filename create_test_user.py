from users.models import User

# Créer un utilisateur de test
user, created = User.objects.get_or_create(
    username='test',
    defaults={
        'email': 'test@example.com',
        'role': 'admin',
        'direction': 'design',
        'is_staff': True,
        'is_superuser': True,
    }
)

if created:
    user.set_password('test123')
    user.save()
    print('✓ Utilisateur créé avec succès!')
else:
    user.set_password('test123')
    user.save()
    print('✓ Utilisateur réinitialisé!')

print(f'Username: test')
print(f'Password: test123')
