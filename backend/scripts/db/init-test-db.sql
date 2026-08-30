-- Creates the logically separate test database on first container init.
-- Runs against the default POSTGRES_DB as the POSTGRES_USER superuser.
SELECT 'CREATE DATABASE trustrail_test'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'trustrail_test')\gexec
