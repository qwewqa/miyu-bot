-- upgrade --
ALTER TABLE "channel" ALTER COLUMN "language" SET DEFAULT '';
ALTER TABLE "channel" ALTER COLUMN "timezone" SET DEFAULT '';
ALTER TABLE "guild" ALTER COLUMN "language" SET DEFAULT '';
ALTER TABLE "guild" ALTER COLUMN "timezone" SET DEFAULT '';
ALTER TABLE "guild" ALTER COLUMN "prefix" SET DEFAULT '';
ALTER TABLE "user" ALTER COLUMN "language" SET DEFAULT '';
ALTER TABLE "user" ALTER COLUMN "timezone" SET DEFAULT '';
-- downgrade --
ALTER TABLE "user" ALTER COLUMN "language" SET DEFAULT 'en';
ALTER TABLE "user" ALTER COLUMN "timezone" SET DEFAULT 'etc/utc';
ALTER TABLE "guild" ALTER COLUMN "language" SET DEFAULT 'en';
ALTER TABLE "guild" ALTER COLUMN "timezone" SET DEFAULT 'etc/utc';
ALTER TABLE "guild" ALTER COLUMN "prefix" SET DEFAULT '!';
ALTER TABLE "channel" ALTER COLUMN "language" SET DEFAULT 'en';
ALTER TABLE "channel" ALTER COLUMN "timezone" SET DEFAULT 'etc/utc';
