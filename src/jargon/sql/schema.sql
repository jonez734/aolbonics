--\echo jargon schema
create schema if not exists jargon;

--\echo jargon.__terms
create table if not exists jargon.__terms (
    slug text primary key,
    term text not null,
    definition text not null,
    origin text,
    datecreated timestamptz not null default now(),
    dateupdated timestamptz not null default now(),
    nsfw boolean not null default true
);

-- Upgrade a table created before the nsfw column existed. Existing terms default to nsfw = true.
alter table jargon.__terms add column if not exists nsfw boolean not null default true;

grant all on jargon.__terms to term, sysop;

--\echo jargon.terms
-- Columns are listed explicitly, with the new nsfw column last. CREATE OR REPLACE VIEW cannot insert a
-- column in the middle of an existing view (it would rename datecreatedlocal), so the order is fixed.
create or replace view jargon.terms as
    select t.slug, t.term, t.definition, t.origin, t.datecreated, t.dateupdated,
        timezone(currentmember.tz, t.datecreated) as datecreatedlocal,
        timezone(currentmember.tz, t.dateupdated) as dateupdatedlocal,
        t.nsfw
    from jargon.__terms as t
    left outer join engine.__member as currentmember on (currentmember.loginid = CURRENT_USER)
;
grant select on jargon.terms to web, term, sysop;
