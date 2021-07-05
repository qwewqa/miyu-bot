-- upgrade --
ALTER TABLE "pitycount" DROP COLUMN "counter";
-- downgrade --
ALTER TABLE "pitycount" ADD "counter" INT NOT NULL  DEFAULT 0;
