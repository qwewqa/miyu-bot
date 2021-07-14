-- upgrade --
ALTER TABLE "gachastate" ADD "sub_pity_counter" INT NOT NULL  DEFAULT 0;
-- downgrade --
ALTER TABLE "gachastate" DROP COLUMN "sub_pity_counter";
