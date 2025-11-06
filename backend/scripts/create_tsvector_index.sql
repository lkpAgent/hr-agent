-- Create GIN index for full-text search on langchain_pg_embedding.document
-- Uses 'simple' configuration to avoid language-specific dependencies
CREATE INDEX IF NOT EXISTS idx_lc_embedding_document_tsv
  ON langchain_pg_embedding
  USING GIN (to_tsvector('simple', document));

-- Optional: JSONB index to accelerate metadata filtering by knowledge_base_id
CREATE INDEX IF NOT EXISTS idx_lc_embedding_cmetadata_gin
  ON langchain_pg_embedding
  USING GIN (cmetadata);

-- Note:
-- For Chinese segmentation, consider installing zhparser or pg_jieba and
-- switching to to_tsvector('zhparser', document). This requires DB extensions.