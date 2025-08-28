-- ProcessGPT Browser Automation Database Schema
-- 초기 데이터베이스 스키마 및 테스트 데이터 생성

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create auth schema for Supabase
CREATE SCHEMA IF NOT EXISTS auth;

-- Create custom types
CREATE TYPE todo_status AS ENUM (
    'PENDING', 'IN_PROGRESS', 'DONE', 'CANCELLED', 'SUBMITTED'
);

CREATE TYPE agent_mode AS ENUM (
    'DRAFT', 'COMPLETE'
);

CREATE TYPE agent_orch AS ENUM (
    'browser_automation_agent', 'web_scraping_agent', 'testing_automation_agent', 'data_collection_agent'
);

CREATE TYPE draft_status AS ENUM (
    'STARTED', 'COMPLETED', 'FB_REQUESTED'
);

-- TodoList table for ProcessGPT tasks
CREATE TABLE IF NOT EXISTS public.todolist (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT NOT NULL DEFAULT 'system',
    proc_inst_id TEXT,
    proc_def_id TEXT,
    activity_id TEXT,
    activity_name TEXT NOT NULL,
    start_date TIMESTAMP DEFAULT NOW(),
    end_date TIMESTAMP,
    description TEXT NOT NULL,
    tool TEXT DEFAULT 'browser-use',
    due_date TIMESTAMP,
    tenant_id TEXT NOT NULL DEFAULT 'default',
    reference_ids TEXT[],
    adhoc BOOLEAN DEFAULT TRUE,
    assignees JSONB DEFAULT '[]'::jsonb,
    duration INTEGER,
    output JSONB,
    retry INTEGER DEFAULT 0,
    consumer TEXT,
    log TEXT,
    draft JSONB,
    project_id UUID,
    feedback JSONB,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    username TEXT DEFAULT 'system',
    status todo_status DEFAULT 'PENDING',
    agent_mode agent_mode DEFAULT 'COMPLETE',
    agent_orch agent_orch DEFAULT 'browser_automation_agent',
    temp_feedback TEXT,
    draft_status draft_status,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Events table for task execution tracking
CREATE TABLE IF NOT EXISTS public.events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    todolist_id UUID NOT NULL REFERENCES public.todolist(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL,
    event_data JSONB NOT NULL,
    context_id VARCHAR(255),
    task_id VARCHAR(255),
    message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_todolist_status_agent ON public.todolist(status, agent_orch);
CREATE INDEX IF NOT EXISTS idx_todolist_proc_inst ON public.todolist(proc_inst_id);
CREATE INDEX IF NOT EXISTS idx_todolist_created_at ON public.todolist(created_at);
CREATE INDEX IF NOT EXISTS idx_events_todolist_id ON public.events(todolist_id);
CREATE INDEX IF NOT EXISTS idx_events_created_at ON public.events(created_at);
CREATE INDEX IF NOT EXISTS idx_events_event_type ON public.events(event_type);

-- Create anonymous role for API access
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
        CREATE ROLE anon;
    END IF;
END
$$;

-- Grant permissions
GRANT USAGE ON SCHEMA public TO anon;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.todolist TO anon;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.events TO anon;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO anon;

-- Row Level Security (RLS) policies
ALTER TABLE public.todolist ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.events ENABLE ROW LEVEL SECURITY;

-- Allow anonymous access for testing
CREATE POLICY "Allow anonymous access to todolist" ON public.todolist
    FOR ALL USING (true);

CREATE POLICY "Allow anonymous access to events" ON public.events
    FOR ALL USING (true);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to automatically update updated_at
CREATE TRIGGER update_todolist_updated_at 
    BEFORE UPDATE ON public.todolist 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Insert test data
INSERT INTO public.todolist (
    activity_name,
    description,
    status,
    agent_orch,
    user_id,
    tenant_id
) VALUES 
(
    'google_search_playwright',
    'Google에서 "playwright" 검색하고 첫 번째 결과 클릭하기',
    'PENDING',
    'browser_automation_agent',
    'test-user-001',
    'test-tenant'
),
(
    'github_homepage_visit',
    'GitHub 홈페이지로 이동하고 주요 정보 수집하기',
    'PENDING', 
    'browser_automation_agent',
    'test-user-001',
    'test-tenant'
),
(
    'naver_weather_search',
    '네이버에서 "날씨" 검색하고 현재 날씨 정보 가져오기',
    'PENDING',
    'browser_automation_agent',
    'test-user-002',
    'test-tenant'
),
(
    'stackoverflow_search',
    'Stack Overflow에서 "browser automation" 검색하기',
    'PENDING',
    'web_scraping_agent',
    'test-user-002',
    'test-tenant'
),
(
    'page_title_extract',
    '현재 페이지의 제목과 메타데이터 추출하기',
    'PENDING',
    'data_collection_agent',
    'test-user-003',
    'test-tenant'
);

-- Insert some completed tasks for history
INSERT INTO public.todolist (
    activity_name,
    description,
    status,
    agent_orch,
    user_id,
    tenant_id,
    output,
    end_date
) VALUES 
(
    'test_completed_task',
    '완료된 테스트 작업',
    'DONE',
    'browser_automation_agent',
    'test-user-001',
    'test-tenant',
    '{"result": "작업이 성공적으로 완료되었습니다", "success": true}'::jsonb,
    NOW() - INTERVAL '1 hour'
);

-- Create a view for active tasks
CREATE OR REPLACE VIEW active_tasks AS
SELECT 
    id,
    activity_name,
    description,
    status,
    agent_orch,
    user_id,
    created_at,
    updated_at
FROM public.todolist
WHERE status IN ('PENDING', 'IN_PROGRESS')
ORDER BY created_at ASC;

-- Grant access to the view
GRANT SELECT ON active_tasks TO anon;

-- Function to get next pending task for an agent
CREATE OR REPLACE FUNCTION get_next_task(agent_type text DEFAULT 'browser_automation_agent')
RETURNS TABLE (
    task_id UUID,
    activity_name TEXT,
    description TEXT,
    user_id TEXT,
    created_at TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        t.id,
        t.activity_name,
        t.description,
        t.user_id,
        t.created_at
    FROM public.todolist t
    WHERE t.status = 'PENDING' 
      AND t.agent_orch = agent_type::agent_orch
    ORDER BY t.created_at ASC
    LIMIT 1;
END;
$$ LANGUAGE plpgsql;

-- Function to update task status
CREATE OR REPLACE FUNCTION update_task_status(
    task_id UUID,
    new_status text,
    result_output jsonb DEFAULT NULL
)
RETURNS BOOLEAN AS $$
BEGIN
    UPDATE public.todolist 
    SET 
        status = new_status::todo_status,
        output = COALESCE(result_output, output),
        end_date = CASE WHEN new_status IN ('DONE', 'CANCELLED') THEN NOW() ELSE end_date END,
        updated_at = NOW()
    WHERE id = task_id;
    
    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

-- Grant execute permissions on functions
GRANT EXECUTE ON FUNCTION get_next_task(text) TO anon;
GRANT EXECUTE ON FUNCTION update_task_status(UUID, text, jsonb) TO anon;

-- Create notification function for real-time updates
CREATE OR REPLACE FUNCTION notify_task_change()
RETURNS trigger AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        PERFORM pg_notify('task_change', json_build_object(
            'operation', 'INSERT',
            'record', row_to_json(NEW)
        )::text);
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        PERFORM pg_notify('task_change', json_build_object(
            'operation', 'UPDATE', 
            'record', row_to_json(NEW),
            'old_record', row_to_json(OLD)
        )::text);
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        PERFORM pg_notify('task_change', json_build_object(
            'operation', 'DELETE',
            'record', row_to_json(OLD)
        )::text);
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for task notifications
CREATE TRIGGER todolist_notify_trigger
    AFTER INSERT OR UPDATE OR DELETE ON public.todolist
    FOR EACH ROW EXECUTE FUNCTION notify_task_change();

-- Log schema creation completion
INSERT INTO public.events (
    todolist_id,
    event_type,
    event_data,
    message
) SELECT
    (SELECT id FROM public.todolist LIMIT 1),
    'system_init',
    json_build_object(
        'action', 'schema_created',
        'timestamp', NOW()::text
    )::jsonb,
    'ProcessGPT Browser Automation database schema initialized successfully';

-- Create simple health check function
CREATE OR REPLACE FUNCTION health_check()
RETURNS json AS $$
BEGIN
    RETURN json_build_object(
        'status', 'healthy',
        'database', 'postgresql',
        'timestamp', NOW(),
        'tables', (
            SELECT json_agg(tablename) 
            FROM pg_tables 
            WHERE schemaname = 'public'
        ),
        'pending_tasks', (
            SELECT COUNT(*) 
            FROM public.todolist 
            WHERE status = 'PENDING'
        )
    );
END;
$$ LANGUAGE plpgsql;

GRANT EXECUTE ON FUNCTION health_check() TO anon;
