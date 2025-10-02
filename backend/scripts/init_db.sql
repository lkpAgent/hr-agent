-- HR Agent Database Initialization Script

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- Create additional schemas if needed
-- CREATE SCHEMA IF NOT EXISTS hr_agent;

-- Set default search path
-- SET search_path TO hr_agent, public;

-- Create custom types if needed
-- CREATE TYPE user_role AS ENUM ('admin', 'hr', 'employee');

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE hr_agent TO hr_agent_user;
GRANT ALL ON SCHEMA public TO hr_agent_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO hr_agent_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO hr_agent_user;

-- Set default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO hr_agent_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO hr_agent_user;