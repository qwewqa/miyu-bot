-- upgrade --
ALTER TABLE "guild" ALTER COLUMN prefix TYPE VARCHAR(63);
-- downgrade --
ALTER TABLE "guild" ALTER COLUMN prefix TYPE VARCHAR(15);
