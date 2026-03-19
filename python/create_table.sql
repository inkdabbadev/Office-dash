-- Run this in Supabase SQL Editor

CREATE TABLE instagram_stats (
    id            BIGSERIAL PRIMARY KEY,
    username      TEXT NOT NULL,
    profile_url   TEXT NOT NULL,
    followers     BIGINT,
    posts         BIGINT,
    scraped_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Optional: index for fast lookups by username
CREATE INDEX idx_instagram_stats_username ON instagram_stats (username);
