-- upgrade --
CREATE TABLE IF NOT EXISTS "collectionentry" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "user_id" BIGINT NOT NULL,
    "gacha_id" INT NOT NULL,
    "table_rate_id" INT NOT NULL,
    "card_id" INT NOT NULL,
    "counter" INT NOT NULL  DEFAULT 0,
    CONSTRAINT "uid_collectione_user_id_8dd8de" UNIQUE ("user_id", "gacha_id", "table_rate_id", "card_id")
);
CREATE INDEX IF NOT EXISTS "idx_collectione_user_id_69fba0" ON "collectionentry" ("user_id");
-- downgrade --
DROP TABLE IF EXISTS "collectionentry";
