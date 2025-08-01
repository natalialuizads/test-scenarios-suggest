CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE scenarios (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    embedding VECTOR(384)
);

CREATE OR REPLACE FUNCTION notify_faiss_update()
RETURNS TRIGGER AS $$
BEGIN
    PERFORM pg_notify('faiss_update', json_build_object(
        'operation', TG_OP,
        'id', NEW.id,
        'title', NEW.title,
        'embedding', NEW.embedding
    )::text);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER faiss_trigger
AFTER INSERT OR UPDATE ON scenarios
FOR EACH ROW EXECUTE FUNCTION notify_faiss_update();