BEGIN;
-- psql -f test.sql -v v1="Conference Name" -v v2="domain.com" -v v3="logo.com/logo.jpg"


INSERT INTO conference (name, url, logo)
    VALUES (:'v1', :'v2', :'v3');

INSERT INTO info (id, name, organization, logo, twitter, facebook, startTime, endTime)
    VALUES (1, :'v1', 'Calligre', :'v3', 'https://twitter.com/usecalligre',
            'https://facebook.com', 1468120162, 1468226562);

INSERT INTO preference (id) VALUES (1);


COMMIT;
