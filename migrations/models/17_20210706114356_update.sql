-- upgrade --
CREATE TABLE IF NOT EXISTS "collectionentry" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "user_id" BIGINT NOT NULL,
    "gacha_id" INT NOT NULL,
    "table_rate_id" INT NOT NULL,
    "card_id" INT NOT NULL,
    "first_pulled" INT NOT NULL  DEFAULT -1,
    "counter" INT NOT NULL  DEFAULT 0,
    CONSTRAINT "uid_collectione_user_id_86bb65" UNIQUE ("user_id", "gacha_id", "table_rate_id", "card_id")
);
CREATE INDEX IF NOT EXISTS "idx_collectione_user_id_69fba0" ON "collectionentry" ("user_id");;
CREATE TABLE IF NOT EXISTS "gachastate" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "user_id" BIGINT NOT NULL,
    "gacha_id" INT NOT NULL,
    "pity_counter" INT NOT NULL  DEFAULT 0,
    "total_counter" INT NOT NULL  DEFAULT 0,
    CONSTRAINT "uid_gachastate_user_id_184477" UNIQUE ("user_id", "gacha_id")
);;
DROP TABLE IF EXISTS "pitycount";
-- downgrade --
DROP TABLE IF EXISTS "collectionentry";
DROP TABLE IF EXISTS "gachastate";
