-- upgrade --
ALTER TABLE "user" ADD "leaks" BOOL;
-- downgrade --
ALTER TABLE "user" DROP COLUMN "leaks";
