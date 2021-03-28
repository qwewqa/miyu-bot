-- upgrade --
ALTER TABLE "channel" ADD "leaks" BOOL;
-- downgrade --
ALTER TABLE "channel" DROP COLUMN "leaks";
