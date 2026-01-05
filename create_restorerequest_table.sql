-- SQL script to create RestoreRequest table manually
-- Use this ONLY if migrations don't work
-- Run: python3 manage.py dbshell < create_restorerequest_table.sql

CREATE TABLE IF NOT EXISTS "blog_restorerequest" (
    "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
    "message" text NULL,
    "status" varchar(10) NOT NULL,
    "created_at" datetime NOT NULL,
    "reviewed_at" datetime NULL,
    "post_id" bigint NOT NULL REFERENCES "blog_post" ("id") DEFERRABLE INITIALLY DEFERRED,
    "writer_id" bigint NOT NULL REFERENCES "blog_user" ("id") DEFERRABLE INITIALLY DEFERRED,
    "reviewed_by_id" bigint NULL REFERENCES "blog_user" ("id") DEFERRABLE INITIALLY DEFERRED
);

CREATE INDEX IF NOT EXISTS "blog_restorerequest_post_id" ON "blog_restorerequest" ("post_id");
CREATE INDEX IF NOT EXISTS "blog_restorerequest_writer_id" ON "blog_restorerequest" ("writer_id");
CREATE INDEX IF NOT EXISTS "blog_restorerequest_reviewed_by_id" ON "blog_restorerequest" ("reviewed_by_id");

-- Update Django migration tracking
INSERT OR IGNORE INTO django_migrations (app, name, applied) VALUES ('blog', '0002_restorerequest', datetime('now'));
