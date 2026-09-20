-- Alert destinations.
--
-- users.webhook_url already exists (Slack/generic). Add an email destination so
-- loop alerts can be delivered by email as well as webhook.

ALTER TABLE users ADD COLUMN IF NOT EXISTS alert_email TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS alerts_enabled BOOLEAN NOT NULL DEFAULT TRUE;
