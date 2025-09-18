-- V1__create_aiteam_schema.sql
-- Create the aiteam schema for the enterprise platform

CREATE SCHEMA IF NOT EXISTS ${schema};

-- Create flyway schema history table in the aiteam schema
CREATE TABLE IF NOT EXISTS ${schema}.flyway_schema_history (
    installed_rank INTEGER NOT NULL,
    version VARCHAR(50),
    description VARCHAR(200) NOT NULL,
    type VARCHAR(20) NOT NULL,
    script VARCHAR(1000) NOT NULL,
    checksum INTEGER,
    installed_by VARCHAR(100) NOT NULL,
    installed_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    execution_time INTEGER NOT NULL,
    success BOOLEAN NOT NULL,
    PRIMARY KEY (installed_rank)
);
