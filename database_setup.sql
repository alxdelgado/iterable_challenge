-- Iterable Challenge: Database Setup
-- Phase 1: Create tables and seed data

-- Drop existing tables if they exist (for clean resets)
DROP TABLE IF EXISTS page_views;
DROP TABLE IF EXISTS customers;

-- Create Customers Table
CREATE TABLE customers (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    email TEXT NOT NULL UNIQUE,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    plan_type TEXT NOT NULL,
    candidate TEXT
);

-- Create Page_views Table
CREATE TABLE page_views (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    user_id INTEGER NOT NULL,
    page TEXT NOT NULL,
    device TEXT NOT NULL,
    browser TEXT NOT NULL,
    location TEXT NOT NULL,
    event_time TIMESTAMP NOT NULL,
    FOREIGN KEY (user_id) REFERENCES customers(id)
);

-- ==========================================
-- Seed Customers Table (15 customers)
-- ==========================================
INSERT INTO customers (email, first_name, last_name, plan_type, candidate) VALUES
('sarah.johnson@email.com', 'Sarah', 'Johnson', 'pro', 'yes'),
('michael.chen@email.com', 'Michael', 'Chen', 'enterprise', 'no'),
('emma.williams@email.com', 'Emma', 'Williams', 'free', 'yes'),
('david.martinez@email.com', 'David', 'Martinez', 'basic', 'no'),
('olivia.brown@email.com', 'Olivia', 'Brown', 'pro', 'yes'),
('james.taylor@email.com', 'James', 'Taylor', 'free', 'no'),
('sophia.anderson@email.com', 'Sophia', 'Anderson', 'enterprise', 'yes'),
('liam.thompson@email.com', 'Liam', 'Thompson', 'basic', 'yes'),
('ava.garcia@email.com', 'Ava', 'Garcia', 'pro', 'no'),
('noah.rodriguez@email.com', 'Noah', 'Rodriguez', 'free', 'yes'),
('isabella.lee@email.com', 'Isabella', 'Lee', 'enterprise', 'no'),
('ethan.white@email.com', 'Ethan', 'White', 'basic', 'no'),
('mia.harris@email.com', 'Mia', 'Harris', 'pro', 'yes'),
('mason.martin@email.com', 'Mason', 'Martin', 'free', 'no'),
('charlotte.perez@email.com', 'Charlotte', 'Perez', 'enterprise', 'yes');

-- ==========================================
-- Seed Page_views Table (40 page view records)
-- ==========================================
INSERT INTO page_views (user_id, page, device, browser, location, event_time) VALUES
(1, 'home page', 'mobile', 'Chrome', 'San Francisco, CA', '2026-01-13 08:15:30'),
(1, 'pricing', 'desktop', 'Firefox', 'San Francisco, CA', '2026-01-13 08:45:12'),
(1, 'features', 'tablet', 'Safari', 'San Francisco, CA', '2026-01-13 09:20:45'),
(2, 'home page', 'desktop', 'Chrome', 'New York, NY', '2026-01-13 09:30:00'),
(2, 'settings', 'mobile', 'Safari', 'New York, NY', '2026-01-13 10:15:22'),
(3, 'pricing', 'desktop', 'Edge', 'Los Angeles, CA', '2026-01-13 10:45:33'),
(3, 'home page', 'mobile', 'Chrome', 'Los Angeles, CA', '2026-01-13 11:00:15'),
(4, 'features', 'desktop', 'Firefox', 'Chicago, IL', '2026-01-13 11:30:42'),
(4, 'blog', 'mobile', 'Chrome', 'Chicago, IL', '2026-01-13 12:00:18'),
(5, 'settings', 'tablet', 'Safari', 'Austin, TX', '2026-01-13 12:30:05'),
(5, 'home page', 'desktop', 'Chrome', 'Austin, TX', '2026-01-13 13:00:27'),
(6, 'pricing', 'mobile', 'Chrome', 'Seattle, WA', '2026-01-13 13:45:50'),
(6, 'features', 'mobile', 'Firefox', 'Seattle, WA', '2026-01-13 14:15:33'),
(7, 'home page', 'desktop', 'Safari', 'Boston, MA', '2026-01-13 14:45:11'),
(7, 'blog', 'tablet', 'Chrome', 'Boston, MA', '2026-01-13 15:20:44'),
(8, 'settings', 'mobile', 'Chrome', 'Denver, CO', '2026-01-13 15:50:26'),
(8, 'pricing', 'desktop', 'Edge', 'Denver, CO', '2026-01-13 16:30:08'),
(9, 'features', 'desktop', 'Chrome', 'Miami, FL', '2026-01-13 16:45:19'),
(9, 'home page', 'mobile', 'Safari', 'Miami, FL', '2026-01-13 17:15:42'),
(10, 'blog', 'tablet', 'Firefox', 'Portland, OR', '2026-01-13 17:45:33'),
(10, 'pricing', 'desktop', 'Chrome', 'Portland, OR', '2026-01-13 18:20:14'),
(11, 'home page', 'mobile', 'Chrome', 'Atlanta, GA', '2026-01-13 18:50:25'),
(11, 'settings', 'desktop', 'Safari', 'Atlanta, GA', '2026-01-13 19:15:38'),
(12, 'features', 'mobile', 'Chrome', 'Phoenix, AZ', '2026-01-13 19:45:07'),
(12, 'blog', 'desktop', 'Firefox', 'Phoenix, AZ', '2026-01-13 20:20:41'),
(13, 'pricing', 'tablet', 'Safari', 'Philadelphia, PA', '2026-01-13 20:50:19'),
(13, 'home page', 'desktop', 'Chrome', 'Philadelphia, PA', '2026-01-13 21:15:53'),
(14, 'settings', 'mobile', 'Chrome', 'Dallas, TX', '2026-01-13 21:45:30'),
(14, 'features', 'tablet', 'Edge', 'Dallas, TX', '2026-01-13 22:20:12'),
(15, 'blog', 'desktop', 'Chrome', 'Houston, TX', '2026-01-13 22:50:44'),
(1, 'blog', 'mobile', 'Safari', 'San Francisco, CA', '2026-01-12 08:30:22'),
(2, 'features', 'tablet', 'Chrome', 'New York, NY', '2026-01-12 09:15:45'),
(3, 'settings', 'desktop', 'Firefox', 'Los Angeles, CA', '2026-01-12 10:00:33'),
(4, 'home page', 'mobile', 'Safari', 'Chicago, IL', '2026-01-12 11:30:18'),
(5, 'blog', 'desktop', 'Chrome', 'Austin, TX', '2026-01-12 12:45:50'),
(6, 'settings', 'mobile', 'Firefox', 'Seattle, WA', '2026-01-12 13:20:27'),
(7, 'pricing', 'tablet', 'Safari', 'Boston, MA', '2026-01-12 14:00:11'),
(8, 'home page', 'desktop', 'Chrome', 'Denver, CO', '2026-01-12 15:15:42'),
(9, 'blog', 'mobile', 'Chrome', 'Miami, FL', '2026-01-12 16:30:19'),
(10, 'features', 'desktop', 'Safari', 'Portland, OR', '2026-01-12 17:45:33');

-- Verify the data was inserted
SELECT 'Customers inserted:' as status;
SELECT COUNT(*) as customer_count FROM customers;

SELECT 'Page views inserted:' as status;
SELECT COUNT(*) as pageview_count FROM page_views;
