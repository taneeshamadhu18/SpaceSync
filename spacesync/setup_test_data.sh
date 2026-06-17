#!/bin/bash

# Setup script for SpaceSync - Create test user and workspace with sample data

# Activate virtual environment
source venv/bin/activate

# Create a superuser (admin/admin)
echo "Creating superuser..."
python manage.py shell << EOF
from django.contrib.auth.models import User
from core.models import Workspace, Project

# Create superuser
if not User.objects.filter(username='admin').exists():
    user = User.objects.create_superuser('admin', 'admin@example.com', 'admin')
    print(f"✓ Superuser created: admin / admin")
else:
    user = User.objects.get(username='admin')
    print(f"✓ Superuser already exists: admin")

# Create test user
if not User.objects.filter(username='testuser').exists():
    test_user = User.objects.create_user('testuser', 'test@example.com', 'testpass123')
    print(f"✓ Test user created: testuser / testpass123")
else:
    test_user = User.objects.get(username='testuser')
    print(f"✓ Test user already exists: testuser")

# Create workspace for test user
if not Workspace.objects.filter(owner=test_user).exists():
    workspace = Workspace.objects.create(
        name='My First Workspace',
        description='Testing workspace for SpaceSync',
        owner=test_user
    )
    print(f"✓ Workspace created: {workspace.name}")
    
    # Create sample projects
    for i in range(3):
        project = Project.objects.create(
            name=f'Sample Project {i+1}',
            description=f'This is sample project number {i+1}',
            workspace=workspace
        )
        print(f"  ✓ Project created: {project.name}")
else:
    workspace = Workspace.objects.filter(owner=test_user).first()
    print(f"✓ Workspace already exists: {workspace.name}")

print("\n✅ Setup complete!")
print("\nTest Credentials:")
print("  Admin: admin / admin")
print("  User: testuser / testpass123")
EOF

echo ""
echo "To get API token:"
echo "  curl -X POST http://localhost:8000/api-token-auth/ \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"username\": \"testuser\", \"password\": \"testpass123\"}'"
