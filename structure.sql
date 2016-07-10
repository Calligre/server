DROP TABLE IF EXISTS info CASCADE;
CREATE TABLE info (
    name            text        NOT NULL,
    logo            text        NOT NULL DEFAULT '',     -- URL
    location        text        NOT NULL DEFAULT '',
    twitter         text        NOT NULL DEFAULT '',
    facebook        text        NOT NULL DEFAULT '',
    other           text        NOT NULL DEFAULT '',
    startTime       bigint      NOT NULL,
    endTime         bigint      NOT NULL
);

DROP TABLE IF EXISTS event CASCADE;
CREATE TABLE event (
    id              serial      PRIMARY KEY,
    name            text        NOT NULL,
    description     text        NOT NULL DEFAULT '',
    stream          integer     NOT NULL DEFAULT 1,      -- 1-indexed for Organizer usage
    location        text        NOT NULL DEFAULT '',
    startTime       bigint      NOT NULL,
    endTime         bigint      NOT NULL
);

DROP TABLE IF EXISTS account CASCADE;
CREATE TABLE account (
    id              serial      PRIMARY KEY,
    name            text        NOT NULL,
    email           text        NOT NULL,
    organization    text        NOT NULL DEFAULT '',
    photo           text        NOT NULL DEFAULT '',
    points          integer     NOT NULL DEFAULT 0,
    facebook        text        NOT NULL DEFAULT '',
    twitter         text        NOT NULL DEFAULT '',
    linkedin        text        NOT NULL DEFAULT '',
    description     text        NOT NULL DEFAULT '',
    private         boolean     NOT NULL DEFAULT FALSE
);

DROP TABLE IF EXISTS subscription CASCADE;
CREATE TABLE subscription (
    account_id      integer     NOT NULL REFERENCES account(id),
    event_id        integer     NOT NULL REFERENCES event(id)
);
