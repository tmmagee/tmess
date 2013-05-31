/* 
 * Adding balance limit column to the account table
 */
ALTER TABLE membership_account ADD COLUMN balance_limit NUMERIC (8,2) NULL;
UPDATE membership_account SET balance_limit=5.00;
ALTER TABLE membership_account ALTER COLUMN balance_limit SET NOT NULL;
