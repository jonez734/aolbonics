-- Privileges the bed's database role needs for jargon. Run once by a privileged role (the zoid6
-- database owner or a superuser), not by jargon --install: installing needs CREATE on the database,
-- and the glossary view reads engine.__member through CURRENT_USER.
--
--   psql -d zoid6 -f sql/grants.sql
--
-- Replace bed_zoid6 below if the bed connects as a different role.

grant create on database zoid6 to bed_zoid6;
grant usage on schema engine to bed_zoid6;
grant select on engine.__member to bed_zoid6;
