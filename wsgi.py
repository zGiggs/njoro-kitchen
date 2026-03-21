import os
from app import app, db, User, MenuItem
from werkzeug.security import generate_password_hash

# Use /tmp directory (writable on Render)
db_path = os.path.join('/tmp', 'njoro_kitchen.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'

# Initialize database
with app.app_context():
    db.create_all()
    print(f"✅ Database created at: {db_path}")
    
    # Create admin if not exists
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
        print("✅ Admin user created")
    
    # Add sample menu items if empty
    if MenuItem.query.count() == 0:
        sample_items = [
            ('Ugali & Sukuma Wiki', 'Traditional maize meal with sautéed collard greens', 250, 'main', 15),
            ('Nyama Choma', 'Grilled goat meat served with kachumbari', 450, 'main', 25),
            ('Chapati', 'Freshly made soft layered flatbread (2 pieces)', 50, 'side', 10),
            ('Rice & Beans', 'Steamed rice with Kenyan beans stew', 200, 'main', 12),
            ('Chicken Stew', 'Tender chicken in rich tomato sauce', 350, 'main', 20),
            ('Fresh Juice', 'Seasonal fresh fruit juice - passion, mango, orange', 150, 'drink', 5),
            ('Mandazi', 'Sweet fried dough pastry (4 pieces)', 80, 'side', 8),
            ('Beef Pilau', 'Spiced rice with beef, cooked in traditional pilau masala', 300, 'special', 18),
        ]
        for name, desc, price, cat, prep in sample_items:
            item = MenuItem(
                name=name,
                description=desc,
                price=price,
                category=cat,
                prep_time=prep,
                is_available=True
            )
            db.session.add(item)
        db.session.commit()
        print(f"✅ Added {len(sample_items)} menu items")
    
    print("✅ Database initialization complete")

# Export for gunicorn
from app import app as application
