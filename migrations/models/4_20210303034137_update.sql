-- upgrade --
ALTER TABLE "user" ADD "prefix" VARCHAR(63) NOT NULL  DEFAULT '';
-- downgrade --
ALTER TABLE "user" DROP COLUMN "prefix";
