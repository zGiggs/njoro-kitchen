-- Create database
CREATE DATABASE IF NOT EXISTS njoro_kitchen;
USE njoro_kitchen;

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE,
    email VARCHAR(100) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    phone VARCHAR(20),
    role ENUM('admin', 'waiter', 'cook') NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    reset_token VARCHAR(100) UNIQUE,
    reset_token_expiry DATETIME,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Menu items table
CREATE TABLE IF NOT EXISTS menu_items (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    category ENUM('main', 'drink', 'special', 'side') NOT NULL,
    prep_time INT DEFAULT 15,
    image_url VARCHAR(255),
    is_available BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Orders table
CREATE TABLE IF NOT EXISTS orders (
    id INT PRIMARY KEY AUTO_INCREMENT,
    order_number VARCHAR(20) UNIQUE NOT NULL,
    table_number INT,
    customer_name VARCHAR(100),
    items JSON,
    total_amount DECIMAL(10,2) NOT NULL,
    status ENUM('pending', 'preparing', 'ready', 'completed') DEFAULT 'pending',
    payment_status ENUM('unpaid', 'paid') DEFAULT 'unpaid',
    payment_time DATETIME,
    special_instructions TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME
);

-- Insert default admin
INSERT INTO users (username, email, password_hash, full_name, role) VALUES
('admin', 'admin@njoro.com', 'scrypt:32768:8:1$m5x7Q7x7Q7x7Q7x7$abc123hash', 'System Admin', 'admin');

-- Insert sample menu items
INSERT INTO menu_items (name, description, price, category, prep_time, image_url) VALUES
('Ugali & Sukuma Wiki', 'Traditional maize meal with sautéed collard greens', 250, 'main', 15, 'https://images.pexels.com/photos/1640777/pexels-photo-1640777.jpeg'),
('Nyama Choma', 'Grilled goat meat with kachumbari', 450, 'main', 25, 'https://www.dreamstime.com/photos-images/nyama-choma.html'),
('Chapati', 'Fresh layered flatbread (2 pieces)', 50, 'side', 10, 'https://images.pexels.com/photos/1030973/pexels-photo-1030973.jpeg'),
('Chicken Stew', 'Tender chicken in rich sauce', 350, 'main', 20, 'https://images.pexels.com/photos/106343/pexels-photo-106343.jpeg'),
('Fresh Juice', 'Passion, mango, or orange', 150, 'drink', 5, 'https://images.pexels.com/photos/338713/pexels-photo-338713.jpeg'),
('Mandazi', 'Sweet fried dough (4 pieces)', 80, 'side', 8, 'https://images.pexels.com/photos/461060/pexels-photo-461060.jpeg'),
('Beef Pilau', 'Spiced rice with beef', 300, 'special', 18, 'https://images.pexels.com/photos/699953/pexels-photo-699953.jpeg'),
('Mango Lassi', 'Sweet yogurt mango drink', 180, 'drink', 5, 'https://images.pexels.com/photos/3023487/pexels-photo-3023487.jpeg'),
('Fish Fry', 'Whole tilapia with ugali', 550, 'special', 25, 'https://images.pexels.com/photos/699953/pexels-photo-699953.jpeg');
