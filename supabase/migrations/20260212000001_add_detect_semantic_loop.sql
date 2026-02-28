-- ============================================
-- MISSING RPC: detect_semantic_loop
-- Called by apps/functions/check/index.ts
-- Uses pgvector cosine distance to find loops
-- Enhanced with action & ngram detection
-- ============================================

-- Drop existing function
DROP FUNCTION IF EXISTS detect_semantic_loop(TEXT, vector, FLOAT);

CREATE OR REPLACE FUNCTION detect_semantic_loop(
  target_session_id TEXT,
  new_embedding vector(384),
  match_threshold FLOAT DEFAULT 0.85,
  action_repeat_limit INTEGER DEFAULT 3,
  ngram_threshold FLOAT DEFAULT 0.5
)
RETURNS TABLE(
  loop_detected BOOLEAN,
  max_similarity FLOAT,
  matching_step INTEGER,
  steps_compared INTEGER,
  action_repeat_count INTEGER,
  ngram_overlap FLOAT,
  semantic_vote BOOLEAN,
  action_vote BOOLEAN,
  ngram_vote BOOLEAN,
  overall_confidence FLOAT
) AS $$
DECLARE
  _max_sim FLOAT := 0;
  _matching_step INTEGER := NULL;
  _count INTEGER := 0;
  _action_repeat_count INTEGER := 0;
  _ngram_overlap FLOAT := 0;
  _semantic_vote BOOLEAN := FALSE;
  _action_vote BOOLEAN := FALSE;
  _ngram_vote BOOLEAN := FALSE;
  _overall_confidence FLOAT := 0;
BEGIN
  -- ============================================
  -- 1. SEMANTIC SIMILARITY CHECK
  -- Uses cosine similarity (1 - distance)
  -- ============================================
  SELECT
    1 - (rh.embedding <=> new_embedding) AS similarity,
    rh.step_number,
    COUNT(*) OVER ()
  INTO _max_sim, _matching_step, _count
  FROM reasoning_history rh
  WHERE rh.session_id = target_session_id
    AND rh.embedding IS NOT NULL
  ORDER BY rh.embedding <=> new_embedding ASC
  LIMIT 1;

  IF _max_sim IS NULL THEN
    _max_sim := 0;
    _count := 0;
  END IF;

  -- Semantic vote: similarity exceeds threshold
  _semantic_vote := _max_sim >= match_threshold;

  -- ============================================
  -- 2. ACTION REPETITION CHECK
  -- Counts how many times the same action repeats
  -- ============================================
  SELECT COALESCE(MAX(cnt), 0)
  INTO _action_repeat_count
  FROM (
    SELECT action, COUNT(*) as cnt
    FROM reasoning_history
    WHERE session_id = target_session_id
      AND action IS NOT NULL
    GROUP BY action
    HAVING COUNT(*) >= action_repeat_limit
  ) repeated;

  -- Action vote: same action repeated N+ times
  _action_vote := _action_repeat_count >= action_repeat_limit;

  -- ============================================
  -- 3. N-GRAM OVERLAP CHECK
  -- Checks if recent reasoning overlaps with previous steps
  -- ============================================
  -- Simplified: Check how many of the last 3 reasoning strings
  -- appear earlier in the session
  SELECT 
    CASE 
      WHEN COUNT(*) > 0 THEN 0.5 + (COUNT(*)::FLOAT * 0.15)
      ELSE 0.0
    END
  INTO _ngram_overlap
  FROM (
    SELECT reasoning, step_number
    FROM reasoning_history rh
    WHERE rh.session_id = target_session_id
      AND rh.reasoning IS NOT NULL
    ORDER BY rh.step_number DESC
    LIMIT 3
  ) recent
  WHERE EXISTS (
    SELECT 1 FROM reasoning_history rh2
    WHERE rh2.session_id = target_session_id
      AND rh2.reasoning = recent.reasoning
      AND rh2.step_number < recent.step_number
  );

  IF _ngram_overlap IS NULL THEN
    _ngram_overlap := 0;
  END IF;

  -- Ngram vote: high overlap with recent steps
  _ngram_vote := _ngram_overlap >= ngram_threshold;

  -- ============================================
  -- 4. VOTING SYSTEM
  -- Combine all detectors with weighted voting
  -- Weights: semantic=1.5, action=1.0, ngram=1.0
  -- Total weight = 3.5, threshold = 0.5
  --
  -- Each detector contributes its confidence * weight:
  --   - semantic: similarity_score * 1.5 (continuous)
  --   - action: 1.0 if fired, 0.0 otherwise (binary)
  --   - ngram: overlap_score * 1.0 (continuous)
  -- ============================================
  _overall_confidence := (
    (CASE WHEN _semantic_vote THEN _max_sim * 1.5 ELSE 0.0 END) +
    (CASE WHEN _action_vote THEN 1.0 ELSE 0.0 END) +
    (CASE WHEN _ngram_vote THEN _ngram_overlap * 1.0 ELSE 0.0 END)
  ) / 3.5;

  -- Use weighted threshold voting (consistent with Python pipeline)
  -- Confidence >= 0.5 means enough detectors agree with enough confidence
  loop_detected := _overall_confidence >= 0.5;

  RETURN QUERY SELECT
    loop_detected,
    _max_sim::FLOAT AS max_similarity,
    _matching_step AS matching_step,
    COALESCE(_count, 0)::INTEGER AS steps_compared,
    _action_repeat_count::INTEGER AS action_repeat_count,
    _ngram_overlap::FLOAT AS ngram_overlap,
    _semantic_vote AS semantic_vote,
    _action_vote AS action_vote,
    _ngram_vote AS ngram_vote,
    _overall_confidence::FLOAT AS overall_confidence;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions
GRANT EXECUTE ON FUNCTION detect_semantic_loop(TEXT, vector, FLOAT, INTEGER, FLOAT) TO service_role;
GRANT EXECUTE ON FUNCTION detect_semantic_loop(TEXT, vector, FLOAT, INTEGER, FLOAT) TO anon;

-- ============================================
-- VECTOR SIMILARITY INDEX
-- HNSW index for cosine searches (works on empty tables,
-- unlike IVFFlat which requires data for clustering).
-- ef_construction=128 gives good recall; m=16 is standard.
-- ============================================
CREATE INDEX IF NOT EXISTS idx_reasoning_embedding
  ON reasoning_history
  USING hnsw (embedding vector_cosine_ops)
  WITH (m = 16, ef_construction = 128);
