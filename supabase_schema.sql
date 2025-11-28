-- Supabase Schema for Agent Logging
-- Run this in your Supabase SQL editor to create the agent_logs table

CREATE TABLE IF NOT EXISTS agent_logs (
    id BIGSERIAL PRIMARY KEY,
    event_type VARCHAR(100) NOT NULL,
    request_id UUID NOT NULL,
    step VARCHAR(255) NOT NULL,
    data JSONB,
    status VARCHAR(50) NOT NULL,
    error TEXT,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_agent_logs_request_id ON agent_logs(request_id);
CREATE INDEX IF NOT EXISTS idx_agent_logs_event_type ON agent_logs(event_type);
CREATE INDEX IF NOT EXISTS idx_agent_logs_status ON agent_logs(status);
CREATE INDEX IF NOT EXISTS idx_agent_logs_timestamp ON agent_logs(timestamp DESC);

-- Create a composite index for common queries
CREATE INDEX IF NOT EXISTS idx_agent_logs_request_timestamp ON agent_logs(request_id, timestamp DESC);

-- Add comments for documentation
COMMENT ON TABLE agent_logs IS 'Stores asynchronous logs for agent processing events';
COMMENT ON COLUMN agent_logs.event_type IS 'Type of event: agent_start, processing_step, agent_complete, api_request, api_response, error';
COMMENT ON COLUMN agent_logs.request_id IS 'Unique identifier for tracking a single request through the system';
COMMENT ON COLUMN agent_logs.step IS 'Processing step name or description';
COMMENT ON COLUMN agent_logs.data IS 'JSON data associated with the event';
COMMENT ON COLUMN agent_logs.status IS 'Status of the event: success, error, in_progress';
COMMENT ON COLUMN agent_logs.error IS 'Error message if status is error';
COMMENT ON COLUMN agent_logs.timestamp IS 'When the event occurred';

-- Enable Row Level Security (RLS) - optional, configure based on your needs
ALTER TABLE agent_logs ENABLE ROW LEVEL SECURITY;

-- Example policy: Allow authenticated users to read all logs
CREATE POLICY "Allow authenticated users to read logs"
    ON agent_logs
    FOR SELECT
    TO authenticated
    USING (true);

-- Example policy: Allow service role to insert logs
CREATE POLICY "Allow service role to insert logs"
    ON agent_logs
    FOR INSERT
    TO service_role
    WITH CHECK (true);
