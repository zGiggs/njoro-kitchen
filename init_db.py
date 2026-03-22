from app import app, db, User, MenuItem, Order
from werkzeug.security import generate_password_hash

with app.app_context():
    # Create all tables
    db.create_all()
    print("✅ All tables created successfully!")
    
    # Check if we already have data
    if MenuItem.query.count() == 0:
        print("📝 Adding menu items...")
        items = [
            ('Ugali & Sukuma Wiki', 'Traditional maize meal with sautéed collard greens', 250, 'main', 15),
            ('Nyama Choma', 'Grilled goat meat served with kachumbari', 450, 'main', 25),
            ('Chapati', 'Freshly made soft layered flatbread', 50, 'side', 10),
            ('Rice & Beans', 'Steamed rice with Kenyan beans stew', 200, 'main', 12),
            ('Chicken Stew', 'Tender chicken in rich tomato sauce', 350, 'main', 20),
            ('Fresh Juice', 'Seasonal fresh fruit juice', 150, 'drink', 5),
            ('Mandazi', 'Sweet fried dough pastry (4 pieces)', 80, 'side', 8),
            ('Beef Pilau', 'Spiced rice with beef', 300, 'special', 18),
        ]
        
        for name, desc, price, cat, prep in items:
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
        print(f"✅ Added {len(items)} menu items!")
    else:
        print(f"ℹ️ Already have {MenuItem.query.count()} menu items")
    
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
        print("✅ Admin user created: admin@njoro.com / Admin@123")
    else:
        print("✅ Admin user already exists")
    
    print("\n📊 Database Summary:")
    print(f"   Users: {User.query.count()}")
    print(f"   Menu Items: {MenuItem.query.count()}")
    print(f"   Orders: {Order.query.count()}")
