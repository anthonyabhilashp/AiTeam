-- V2__create_profile_table.sql
-- Create the profile table for user profiles

CREATE TABLE IF NOT EXISTS ${schema}.profiles (
    user_id VARCHAR(36) PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    username VARCHAR(255) NOT NULL UNIQUE,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_profiles_email ON ${schema}.profiles(email);
CREATE INDEX IF NOT EXISTS idx_profiles_username ON ${schema}.profiles(username);
