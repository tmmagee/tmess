CREATE TABLE "membership_member_job_interests" (
"id" serial NOT NULL PRIMARY KEY,
"member_id" integer NOT NULL,
"job_id" integer NOT NULL REFERENCES "scheduling_job" ("id") DEFERRABLE INITIALLY DEFERRED,
UNIQUE ("member_id", "job_id")
)   
;
CREATE TABLE "membership_member_skills" (
"id" serial NOT NULL PRIMARY KEY,
"member_id" integer NOT NULL,
"skill_id" integer NOT NULL REFERENCES "scheduling_skill" ("id") DEFERRABLE INITIALLY DEFERRED,
UNIQUE ("member_id", "skill_id")
)   
;

ALTER TABLE "membership_member_job_interests" ADD CONSTRAINT "member_id_refs_id_16d76695" FOREIGN KEY ("member_id") REFERENCES "membership_member" ("id") DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE "membership_member_skills" ADD CONSTRAINT "member_id_refs_id_3260e6ef" FOREIGN KEY ("member_id") REFERENCES "membership_member" ("id") DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE "membership_member" ADD COLUMN "availability" integer;
ALTER TABLE "membership_member" ADD COLUMN "extra_info" varchar(255);
