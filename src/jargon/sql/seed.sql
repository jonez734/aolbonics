--\echo jargon seed terms
insert into jargon.__terms (slug, term, definition, origin) values
    ('wtf', 'WTF', 'What the f***. An exclamation of surprise, confusion, or disbelief.', 'Internet slang, widely used since the 1990s.'),
    ('lart', 'LART', 'Luser Attitude Readjustment Tool. A blunt instrument (often a swift kick or a clue-by-four) for correcting a user who has behaved badly.', 'Humorous Unix and Usenet culture term.')
on conflict (slug) do nothing;
