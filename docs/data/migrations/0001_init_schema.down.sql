-- 0001_init_schema.down.sql
-- 回滾 0001。反序 drop；CASCADE 連同 policy/index 一併移除。

DROP TABLE IF EXISTS audit_event     CASCADE;
DROP TABLE IF EXISTS message         CASCADE;
DROP TABLE IF EXISTS knowledge_chunk CASCADE;
DROP TABLE IF EXISTS interaction     CASCADE;
DROP TABLE IF EXISTS contact         CASCADE;
DROP TABLE IF EXISTS tenant          CASCADE;

DROP FUNCTION IF EXISTS current_tenant();

-- 注意：extension (vector / pgcrypto) 不在此 drop，避免影響同庫其他物件。
