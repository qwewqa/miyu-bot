-- upgrade --
ALTER TABLE "channel" DROP COLUMN "name";
ALTER TABLE "guild" DROP COLUMN "name";
ALTER TABLE "user" DROP COLUMN "name";
-- downgrade --
ALTER TABLE "user" ADD "name" VARCHAR(255) NOT NULL;
ALTER TABLE "guild" ADD "name" VARCHAR(255) NOT NULL;
ALTER TABLE "channel" ADD "name" VARCHAR(255) NOT NULL;
