ALTER TABLE membership_member RENAME COLUMN equity_held TO member_owner_equity_held;
ALTER TABLE membership_member ADD COLUMN membership_fund_equity_held numeric(8,2) NULL DEFAULT 0.00;
UPDATE membership_member SET membership_fund_equity_held=0;
ALTER TABLE membership_member ALTER COLUMN membership_fund_equity_held SET NOT NULL;

ALTER TABLE revision_memberrevision RENAME COLUMN equity_held TO member_owner_equity_held;
ALTER TABLE revision_memberrevision ADD COLUMN membership_fund_equity_held numeric(8,2) NULL DEFAULT 0.00;
UPDATE revision_memberrevision SET membership_fund_equity_held=0;
ALTER TABLE revision_memberrevision ALTER COLUMN membership_fund_equity_held SET NOT NULL;

ALTER TABLE membership_account ADD COLUMN account_type varchar(1) NULL DEFAULT 'm';
UPDATE membership_account SET account_type='m';
ALTER TABLE membership_account ALTER COLUMN account_type SET NOT NULL;

