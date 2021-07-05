-- upgrade --
ALTER TABLE "pitycount" ADD "counter" INT NOT NULL  DEFAULT 0;
-- downgrade --
ALTER TABLE "pitycount" DROP COLUMN "counter";
