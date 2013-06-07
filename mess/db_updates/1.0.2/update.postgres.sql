/* 
 * Adding balance limit column to the account table
 */
ALTER TABLE membership_member ADD COLUMN hours_balance NUMERIC (5,2) NULL;
UPDATE membership_member SET hours_balance=0.00;
ALTER TABLE membership_member ALTER COLUMN hours_balance SET NOT NULL;
