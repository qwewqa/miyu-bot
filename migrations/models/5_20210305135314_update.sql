-- upgrade --
ALTER TABLE "channel" ADD "loop" INT;
-- downgrade --
ALTER TABLE "channel" DROP COLUMN "loop";
