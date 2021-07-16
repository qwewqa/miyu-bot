-- upgrade --
ALTER TABLE "gachastate" DROP COLUMN "sub_pity_counter";
-- downgrade --
ALTER TABLE "gachastate" ADD "sub_pity_counter" INT NOT NULL  DEFAULT 0;
