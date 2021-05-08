-- upgrade --
CREATE TABLE IF NOT EXISTS "commandusagecount" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "guild_id" BIGINT NOT NULL,
    "name" VARCHAR(31) NOT NULL,
    "counter" INT NOT NULL  DEFAULT 0,
    CONSTRAINT "uid_commandusag_guild_i_394d5d" UNIQUE ("guild_id", "name")
);;
CREATE UNIQUE INDEX "uid_pitycount_user_id_640261" ON "pitycount" ("user_id", "gacha_id");
-- downgrade --
DROP INDEX "uid_pitycount_user_id_640261";
DROP TABLE IF EXISTS "commandusagecount";
