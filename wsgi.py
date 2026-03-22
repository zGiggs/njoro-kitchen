import os
import sys
from app import app, db

# Force SQLite path to /tmp (writable on Render)
db_path = os.path.join('/tmp', 'njoro_kitchen.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'

print(f"🔵 Database path: {db_path}")

# Initialize database
with app.app_context():
    # Import models inside app context (after app is configured)
    from app import User, MenuItem, Order
    
    # Create all tables
    db.create_all()
    print("✅ Tables created")
    
    # Create admin user
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
    
    # Add ALL menu items (28 items)
    if MenuItem.query.count() == 0:
        print("📝 Adding all menu items...")
        items = [
            ('Ugali & Sukuma Wiki', 'Traditional maize meal with sautéed collard greens', 250, 'main', 15),
            ('Nyama Choma', 'Grilled goat meat served with kachumbari', 450, 'main', 25),
            ('Chapati', 'Freshly made soft layered flatbread', 50, 'side', 10),
            ('Rice & Beans', 'Steamed rice with Kenyan beans stew', 200, 'main', 12),
            ('Chicken Stew', 'Tender chicken in rich tomato sauce', 350, 'main', 20),
            ('Fresh Juice', 'Seasonal fresh fruit juice', 150, 'drink', 5),
            ('Mandazi', 'Sweet fried dough pastry (4 pieces)', 80, 'side', 8),
            ('Beef Pilau', 'Spiced rice with beef', 300, 'special', 18),
            ('Matoke', 'Green bananas cooked in coconut milk', 280, 'main', 20),
            ('Samosa', 'Crispy pastry filled with spiced meat (3 pieces)', 120, 'appetizer', 10),
            ('Grilled Fish', 'Whole tilapia grilled with herbs', 550, 'main', 30),
            ('Mukimo', 'Mashed potatoes with peas and corn', 220, 'side', 15),
            ('Kachumbari', 'Fresh tomato and onion salsa', 80, 'side', 5),
            ('Chai', 'Traditional Kenyan tea', 70, 'drink', 5),
            ('Pilipili', 'Spicy chili sauce', 30, 'condiment', 2),
            ('Sausage', 'Beef sausage (2 pieces)', 150, 'side', 8),
            ('Chips', 'French fries', 120, 'side', 12),
            ('Chicken Wings', 'Spicy grilled chicken wings', 300, 'appetizer', 20),
            ('Vegetable Curry', 'Mixed vegetables in coconut curry', 280, 'main', 18),
            ('Lentil Soup', 'Hearty lentil soup', 150, 'appetizer', 10),
            ('Pancakes', 'Fluffy pancakes with honey', 180, 'breakfast', 12),
            ('Omelette', 'Three-egg omelette with toast', 200, 'breakfast', 10),
            ('Burger', 'Beef burger with fries', 350, 'main', 15),
            ('Shawarma', 'Chicken shawarma wrap', 280, 'main', 12),
            ('Fruit Salad', 'Mixed fresh fruits', 160, 'dessert', 5),
            ('Ice Cream', 'Vanilla ice cream', 100, 'dessert', 3),
            ('Brownie', 'Chocolate brownie', 120, 'dessert', 5),
            ('Coffee', 'Fresh brewed coffee', 90, 'drink', 5)
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
    
    print("\n📊 Database Summary:")
    print(f"   Users: {User.query.count()}")
    print(f"   Menu Items: {MenuItem.query.count()}")
    print(f"   Orders: {Order.query.count() if hasattr(Order, 'query') else 0}")
    print("✅ Database ready")

# Application instance for WSGI
application = app

if __name__ == "__main__":
    app.run()
