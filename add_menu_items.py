from app import app, db, MenuItem

with app.app_context():
    # Check how many items we have now
    current_count = MenuItem.query.count()
    print(f"Current items: {current_count}")
    
    # Only add if we have less than 10 items
    if current_count < 10:
        items = [
            ('Ugali & Sukuma Wiki', 'Traditional maize meal with sautéed collard greens', 250, 'main', 15),
            ('Nyama Choma', 'Grilled goat meat served with kachumbari', 450, 'main', 25),
            ('Chapati', 'Freshly made soft layered flatbread', 50, 'side', 10),
            ('Rice & Beans', 'Steamed rice with Kenyan beans stew', 200, 'main', 12),
            ('Chicken Stew', 'Tender chicken in rich tomato sauce', 350, 'main', 20),
            ('Beef Stew', 'Slow-cooked beef in rich gravy', 380, 'main', 25),
            ('Fish Fry', 'Whole fried tilapia with ugali', 550, 'main', 25),
            ('Matoke', 'Mashed green bananas with onions', 280, 'main', 20),
            ('Mukimo', 'Mashed potatoes with greens and maize', 220, 'main', 18),
            ('Githeri', 'Traditional maize and beans mix', 180, 'main', 15),
            ('Fresh Passion Juice', 'Pure passion fruit juice', 150, 'drink', 5),
            ('Mango Lassi', 'Sweet yogurt mango drink', 180, 'drink', 5),
            ('Masala Chai', 'Traditional spiced tea', 80, 'drink', 3),
            ('Kenyan Coffee', 'Rich AA coffee', 150, 'drink', 5),
            ('Fresh Orange Juice', 'Squeezed fresh oranges', 150, 'drink', 5),
            ('Dawa Cocktail', 'Honey, lemon and ginger drink', 250, 'drink', 5),
            ('Virgin Mojito', 'Mint and lime refresher', 220, 'drink', 5),
            ('Stoney Tangawizi', 'Ginger flavored soda', 120, 'drink', 2),
            ('Beef Pilau', 'Spiced rice with beef', 300, 'special', 18),
            ('Chicken Biryani', 'Spiced rice with chicken', 450, 'special', 25),
            ('Omena', 'Silver cyprinid with ugali', 320, 'special', 20),
            ('Goat Stew', 'Slow-cooked goat meat', 480, 'special', 30),
            ('Kachumbari', 'Fresh tomato-onion salsa', 80, 'side', 5),
            ('Samosas', 'Crispy meat pastries (3pcs)', 150, 'side', 10),
            ('Chips Masala', 'Spiced french fries', 180, 'side', 12),
            ('Viazi Karai', 'Fried potato bites', 150, 'side', 12),
            ('Coleslaw', 'Fresh cabbage salad', 80, 'side', 5),
        ]
        
        for name, desc, price, cat, prep in items:
            # Check if item already exists
            existing = MenuItem.query.filter_by(name=name).first()
            if not existing:
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
        print(f"✅ Added items. Total now: {MenuItem.query.count()}")
    else:
        print(f"✅ Already have {current_count} items. No changes needed.")
    
    # Show summary
    from sqlalchemy import func
    categories = db.session.query(MenuItem.category, func.count()).group_by(MenuItem.category).all()
    print("\n📊 Menu Summary:")
    for cat, count in categories:
        print(f"   {cat}: {count} items")
