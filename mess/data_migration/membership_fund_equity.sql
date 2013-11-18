ALTER TABLE membership_member RENAME COLUMN equity_held TO personal_equity_held;
ALTER TABLE membership_member ADD COLUMN membership_fund_equity_held numeric(8,2) NULL DEFAULT 0.00;
UPDATE membership_member SET membership_fund_equity_held=0;
ALTER TABLE membership_member ALTER COLUMN membership_fund_equity_held SET NOT NULL;

ALTER TABLE revision_memberrevision RENAME COLUMN equity_held TO personal_equity_held;
ALTER TABLE revision_memberrevision ADD COLUMN membership_fund_equity_held numeric(8,2) NULL DEFAULT 0.00;
UPDATE revision_memberrevision SET membership_fund_equity_held=0;
ALTER TABLE revision_memberrevision ALTER COLUMN membership_fund_equity_held SET NOT NULL;
