-- Initialize pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create documents table
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename TEXT NOT NULL,
    file_type TEXT NOT NULL,
    file_size_bytes BIGINT NOT NULL,
    uploaded_by UUID,
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    processed BOOLEAN DEFAULT FALSE,
    metadata JSONB DEFAULT '{}'::jsonb,
    CONSTRAINT valid_file_size CHECK (file_size_bytes > 0)
);

-- Create document chunks table with vector embeddings
CREATE TABLE IF NOT EXISTS document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding vector(768),  -- Adjust dimension based on embedding model
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_chunk_index CHECK (chunk_index >= 0)
);

-- Create index for vector similarity search
CREATE INDEX IF NOT EXISTS document_chunks_embedding_idx 
ON document_chunks USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT,
    role TEXT DEFAULT 'user',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}'::jsonb,
    CONSTRAINT valid_email CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

-- Create conversations table
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    title TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Create messages table
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    model TEXT,
    tokens_used INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Create audit log table for FISMA compliance
CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    user_id UUID REFERENCES users(id),
    action TEXT NOT NULL,
    resource_type TEXT,
    resource_id TEXT,
    ip_address INET,
    user_agent TEXT,
    status_code INTEGER,
    request_id TEXT,
    details JSONB DEFAULT '{}'::jsonb
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_documents_uploaded_by ON documents(uploaded_by);
CREATE INDEX IF NOT EXISTS idx_documents_uploaded_at ON documents(uploaded_at);
CREATE INDEX IF NOT EXISTS idx_document_chunks_document_id ON document_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_user_id ON audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON audit_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_log_action ON audit_log(action);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for conversations table
CREATE TRIGGER update_conversations_updated_at
    BEFORE UPDATE ON conversations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create view for document statistics
CREATE OR REPLACE VIEW document_stats AS
SELECT
    COUNT(*) as total_documents,
    SUM(file_size_bytes) as total_size_bytes,
    AVG(file_size_bytes) as avg_size_bytes,
    COUNT(DISTINCT file_type) as unique_file_types,
    COUNT(CASE WHEN processed = TRUE THEN 1 END) as processed_documents
FROM documents;

-- Create view for user activity
CREATE OR REPLACE VIEW user_activity AS
SELECT
    u.id,
    u.email,
    u.full_name,
    COUNT(DISTINCT c.id) as conversation_count,
    COUNT(DISTINCT m.id) as message_count,
    MAX(u.last_login) as last_activity
FROM users u
LEFT JOIN conversations c ON u.id = c.user_id
LEFT JOIN messages m ON c.id = m.conversation_id
GROUP BY u.id, u.email, u.full_name;

-- AC-8: System Use Notification Acknowledgments
-- Tracks user acknowledgments of system use warning per NIST SP 800-53 Rev 5
CREATE TABLE IF NOT EXISTS system_use_acknowledgments (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    banner_version VARCHAR(10) NOT NULL,
    acknowledged_at TIMESTAMP WITH TIME ZONE NOT NULL,
    ip_address VARCHAR(45),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_system_use_ack_user 
ON system_use_acknowledgments(user_id);

CREATE INDEX IF NOT EXISTS idx_system_use_ack_date 
ON system_use_acknowledgments(acknowledged_at);

COMMENT ON TABLE system_use_acknowledgments IS 
'AC-8: Records user acknowledgments of system use notification per NIST SP 800-53 Rev 5';

-- Grant appropriate permissions
-- Note: Adjust these based on your database user configuration
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO fedchat_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO fedchat_user;

-- Log initialization
DO $$
BEGIN
    RAISE NOTICE 'FedChat database initialized successfully';
    RAISE NOTICE 'pgvector extension enabled for RAG functionality';
    RAISE NOTICE 'Tables created: documents, document_chunks, users, conversations, messages, audit_log';
END $$;
