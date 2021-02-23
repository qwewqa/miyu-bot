-- upgrade --
CREATE TABLE IF NOT EXISTS "channel" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "name" VARCHAR(255) NOT NULL,
    "timezone_preference" VARCHAR(31) NOT NULL  DEFAULT '',
    "language_preference" VARCHAR(15) NOT NULL  DEFAULT ''
);
CREATE TABLE IF NOT EXISTS "guild" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "name" VARCHAR(255) NOT NULL,
    "timezone_preference" VARCHAR(31) NOT NULL  DEFAULT '',
    "language_preference" VARCHAR(15) NOT NULL  DEFAULT '',
    "prefix_preference" VARCHAR(15) NOT NULL  DEFAULT ''
);
CREATE TABLE IF NOT EXISTS "user" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "name" VARCHAR(255) NOT NULL,
    "timezone_preference" VARCHAR(31) NOT NULL  DEFAULT '',
    "language_preference" VARCHAR(15) NOT NULL  DEFAULT ''
);
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(20) NOT NULL,
    "content" JSONB NOT NULL
);
