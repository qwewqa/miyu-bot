-- upgrade --
ALTER TABLE "commandusagecount" DROP CONSTRAINT  "uid_commandusag_guild_i_394d5d";
ALTER TABLE "commandusagecount" ADD "date" DATE NOT NULL  DEFAULT '2021-01-01';
CREATE UNIQUE INDEX "uid_commandusag_guild_i_c9aef2" ON "commandusagecount" ("guild_id", "name", "date");
CREATE TABLE IF NOT EXISTS "generalusagecount" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "name" TEXT NOT NULL,
    "date" DATE NOT NULL,
    "counter" INT NOT NULL  DEFAULT 0,
    CONSTRAINT "uid_generalusag_name_f80248" UNIQUE ("name", "date")
);;
-- downgrade --
CREATE UNIQUE INDEX "uid_commandusag_guild_i_394d5d" ON "commandusagecount" ("guild_id", "name");
DROP INDEX "uid_commandusag_guild_i_c9aef2";
ALTER TABLE "commandusagecount" DROP COLUMN "date";
DROP TABLE IF EXISTS "generalusagecount";
