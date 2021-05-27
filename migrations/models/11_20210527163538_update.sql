-- upgrade --
ALTER TABLE "channel" ADD "server" SMALLINT;
ALTER TABLE "guild" ADD "server" SMALLINT;
ALTER TABLE "user" ADD "server" SMALLINT;
-- downgrade --
ALTER TABLE "user" DROP COLUMN "server";
ALTER TABLE "guild" DROP COLUMN "server";
ALTER TABLE "channel" DROP COLUMN "server";
