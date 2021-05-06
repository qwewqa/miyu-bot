-- upgrade --
CREATE TABLE IF NOT EXISTS "pitycount" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "user_id" BIGSERIAL NOT NULL,
    "gacha_id" INT NOT NULL,
    "counter" INT NOT NULL  DEFAULT 0
);
-- downgrade --
DROP TABLE IF EXISTS "pitycount";
