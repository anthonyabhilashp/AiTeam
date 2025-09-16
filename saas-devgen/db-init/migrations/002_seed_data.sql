-- Migration 002: Seed Data for Demo Environment
-- Default tenant and user setup
-- Version: 1.0.1
-- Date: 2025-09-12

-- Insert demo tenant
INSERT INTO tenants (id, name, org_id, status, subscription_plan)
VALUES (1, 'Demo Organization', 'demo-org-001', 'active', 'enterprise')
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    org_id = EXCLUDED.org_id,
    updated_at = CURRENT_TIMESTAMP;

-- Insert demo user
INSERT INTO users (id, tenant_id, username, email, roles, status)
VALUES (1, 1, 'demo', 'demo@example.com', ARRAY['admin', 'developer'], 'active')
ON CONFLICT (tenant_id, username) DO UPDATE SET
    email = EXCLUDED.email,
    roles = EXCLUDED.roles,
    updated_at = CURRENT_TIMESTAMP;

-- Insert demo tenant settings with OpenRouter configuration
INSERT INTO tenant_settings (tenant_id, ai_provider, ai_model, api_key, additional_config)
VALUES (1, 'openrouter', 'deepseek/deepseek-chat-v3.1:free', '', 
        '{"base_url": "https://openrouter.ai/api/v1", "supports_functions": true, "max_tokens": 4096}')
ON CONFLICT (tenant_id) DO UPDATE SET
    ai_provider = EXCLUDED.ai_provider,
    ai_model = EXCLUDED.ai_model,
    additional_config = EXCLUDED.additional_config,
    updated_at = CURRENT_TIMESTAMP;

-- Reset sequences to ensure proper ID generation
SELECT setval('tenants_id_seq', (SELECT COALESCE(MAX(id), 1) FROM tenants));
SELECT setval('users_id_seq', (SELECT COALESCE(MAX(id), 1) FROM users));

-- Record migration
INSERT INTO schema_migrations (version, description) 
VALUES ('002', 'Seed data for demo environment with OpenRouter configuration')
ON CONFLICT (version) DO NOTHING;
