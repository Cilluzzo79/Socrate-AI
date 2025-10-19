-- Reset database: drop all tables and recreate schema
-- WARNING: This will DELETE ALL DATA!

-- Drop all tables
DROP TABLE IF EXISTS chat_sessions CASCADE;
DROP TABLE IF EXISTS documents CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- Tables will be recreated by the Flask app on next startup via init_db()
