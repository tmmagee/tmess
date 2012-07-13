ALTER TABLE "membership_account" ADD COLUMN "max_allowed_to_owe" numeric(8,2) NULL;
UPDATE membership_account SET max_allowed_to_owe=5.00;
ALTER TABLE "membership_account" ALTER COLUMN "max_allowed_to_owe" SET NOT NULL;
