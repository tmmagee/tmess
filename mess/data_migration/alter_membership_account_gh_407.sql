ALTER TABLE "membership_account" ADD COLUMN "balance_limit" numeric(8,2) NULL;
UPDATE membership_account SET balance_limit=5.00;
ALTER TABLE "membership_account" ALTER COLUMN "balance_limit" SET NOT NULL;
