BEGIN;

CREATE TABLE info (
    id              serial      PRIMARY KEY,             -- should only be one of these
    name            text        NOT NULL,
    logo            text        NOT NULL DEFAULT '',     -- URL
    location        text        NOT NULL DEFAULT '',
    twitter         text        NOT NULL DEFAULT '',
    facebook        text        NOT NULL DEFAULT '',
    other           text        NOT NULL DEFAULT '',
    startTime       bigint      NOT NULL,
    endTime         bigint      NOT NULL
);

CREATE TABLE event (
    id              serial      PRIMARY KEY,
    name            text        NOT NULL,
    description     text        NOT NULL DEFAULT '',
    stream          integer     NOT NULL DEFAULT 1,      -- 1-indexed for Organizer usage
    location        text        NOT NULL DEFAULT '',
    startTime       bigint      NOT NULL,
    endTime         bigint      NOT NULL
);

CREATE TABLE account (
    id              text        PRIMARY KEY,
    first_name      text        NOT NULL,
    last_name       text        NOT NULL,
    email           text        NOT NULL,
    organization    text        NOT NULL DEFAULT '',
    photo           text        NOT NULL DEFAULT '',
    points          integer     NOT NULL DEFAULT 0,
    facebook        text        NOT NULL DEFAULT '',
    twitter         text        NOT NULL DEFAULT '',
    linkedin        text        NOT NULL DEFAULT '',
    description     text        NOT NULL DEFAULT '',
    private         boolean     NOT NULL DEFAULT FALSE,
    capabilities    integer     NOT NULL DEFAULT 1
        CHECK (0 < capabilities AND capabilities < 8)     -- 1: read, 2: write, 4: admin
);

CREATE TABLE subscription (
    id              serial      PRIMARY KEY,
    account_id      text        NOT NULL REFERENCES account(id) ON DELETE CASCADE,
    event_id        integer     NOT NULL REFERENCES event(id) ON DELETE CASCADE
);

CREATE TABLE broadcast (
    id              serial      PRIMARY KEY,
    message         text        NOT NULL,
    expiryTime      bigint      NOT NULL
);

CREATE TABLE preference (
    id              serial      PRIMARY KEY,             -- should only be one of these
    cards           boolean     NOT NULL DEFAULT TRUE,
    info            boolean     NOT NULL DEFAULT TRUE,
    newsfeed        boolean     NOT NULL DEFAULT TRUE,
    facebook        boolean     NOT NULL DEFAULT TRUE,
    twitter         boolean     NOT NULL DEFAULT TRUE,
    reposts         boolean     NOT NULL DEFAULT TRUE
);
