import os
import sys
from app import app, db, User, MenuItem
from werkzeug.security import generate_password_hash

# Force SQLite path to /tmp (writable on Render)
db_path = os.path.join('/tmp', 'njoro_kitchen.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'

print(f"🔵 Database path: {db_path}")

# Initialize database
with app.app_context():
    db.create_all()
    print("✅ Tables created")
    
    # Create admin
    if User.query.filter_by(role='admin').first() is None:
        admin = User(
            username='admin',
            email='admin@njoro.com',
            full_name='System Administrator',
            role='admin',
            is_active=True
        )
        admin.set_password('Admin@123')
        db.session.add(admin)
        db.session.commit()
        print("✅ Admin created")
    
    # Add sample menu items
    if MenuItem.query.count() == 0:
        items = [
            ('Ugali & Sukuma Wiki', 'Traditional maize meal with sautéed collard greens', 250, 'main', 15),
            ('Nyama Choma', 'Grilled goat meat served with kachumbari', 450, 'main', 25),
            ('Chapati', 'Freshly made soft layered flatbread', 50, 'side', 10),
            ('Rice & Beans', 'Steamed rice with Kenyan beans stew', 200, 'main', 12),
        ]
        for name, desc, price, cat, prep in items:
            item = MenuItem(name=name, description=desc, price=price, category=cat, prep_time=prep, is_available=True)
            db.session.add(item)
        db.session.commit()
        print(f"✅ Added {len(items)} menu items")
    
    print("✅ Database ready")

from app import app as application
