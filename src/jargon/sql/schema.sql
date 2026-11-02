--\echo jargon schema
create schema if not exists jargon;

--\echo jargon.__terms
create table if not exists jargon.__terms (
    slug text primary key,
    term text not null,
    definition text not null,
    origin text,
    nsfw boolean not null default true,
    datecreated timestamptz not null default now(),
    dateupdated timestamptz not null default now()
);

-- Upgrade a table created before the nsfw column existed. Existing terms default to nsfw = true.
alter table jargon.__terms add column if not exists nsfw boolean not null default true;

grant all on jargon.__terms to term, sysop;

--\echo jargon.terms
create or replace view jargon.terms as
    select t.*,
        timezone(currentmember.tz, t.datecreated) as datecreatedlocal,
        timezone(currentmember.tz, t.dateupdated) as dateupdatedlocal
    from jargon.__terms as t
    left outer join engine.__member as currentmember on (currentmember.loginid = CURRENT_USER)
;
grant select on jargon.terms to web, term, sysop;
