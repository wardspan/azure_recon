-- Initialize Azure Recon database schema
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Table to store scan results history
CREATE TABLE IF NOT EXISTS scan_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id VARCHAR(255) NOT NULL,
    scan_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    scan_data JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table to store authentication sessions (optional)
CREATE TABLE IF NOT EXISTS auth_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_accessed TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table to store generated reports
CREATE TABLE IF NOT EXISTS generated_reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scan_result_id UUID REFERENCES scan_results(id) ON DELETE CASCADE,
    report_type VARCHAR(50) NOT NULL, -- 'markdown' or 'pdf'
    file_path VARCHAR(500) NOT NULL,
    file_size BIGINT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_scan_results_tenant_timestamp ON scan_results(tenant_id, scan_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_auth_sessions_tenant ON auth_sessions(tenant_id);
CREATE INDEX IF NOT EXISTS idx_auth_sessions_expires ON auth_sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_generated_reports_scan_id ON generated_reports(scan_result_id);

-- Update timestamp trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add update trigger to scan_results
CREATE TRIGGER update_scan_results_updated_at 
    BEFORE UPDATE ON scan_results 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Add sample data retention policy (optional - uncomment if needed)
-- This function can be called periodically to clean up old data
/*
CREATE OR REPLACE FUNCTION cleanup_old_data()
RETURNS void AS $$
BEGIN
    -- Delete scan results older than 90 days
    DELETE FROM scan_results 
    WHERE created_at < NOW() - INTERVAL '90 days';
    
    -- Delete expired auth sessions
    DELETE FROM auth_sessions 
    WHERE expires_at < NOW();
    
    -- Delete orphaned reports
    DELETE FROM generated_reports 
    WHERE scan_result_id NOT IN (SELECT id FROM scan_results);
END;
$$ LANGUAGE plpgsql;
*/