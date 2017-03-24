BEGIN;

CREATE TABLE info (
    id              serial      PRIMARY KEY,             -- should only be one of these
    name            text        NOT NULL,
    organization    text        NOT NULL,
    map             text        NOT NULL DEFAULT '',     -- URL
    package         text        NOT NULL DEFAULT '',     -- URL
    background_logo text        NOT NULL DEFAULT '',     -- URL
    logo            text        NOT NULL DEFAULT '',     -- URL
    logo_square     text        NOT NULL DEFAULT '',     -- URL
    icon            text        NOT NULL DEFAULT '',     -- URL
    color_primary   text        NOT NULL DEFAULT '#000',
    color_secondary text        NOT NULL DEFAULT '#000',
    twitter         text        NOT NULL DEFAULT '',
    facebook        text        NOT NULL DEFAULT '',
    startTime       bigint      NOT NULL,
    endTime         bigint      NOT NULL
);

CREATE TABLE contact (
    id              serial      PRIMARY KEY,
    info_id         integer     NOT NULL REFERENCES info(id) ON DELETE CASCADE,
    name            text        NOT NULL,
    phone           text        NOT NULL
);

CREATE TABLE card (
    id              serial      PRIMARY KEY,
    info_id         integer     NOT NULL REFERENCES info(id) ON DELETE CASCADE,
    data            text        NOT NULL
);

CREATE TABLE location (
    id              serial      PRIMARY KEY,
    info_id         integer     NOT NULL REFERENCES info(id) ON DELETE CASCADE,
    name            text        NOT NULL,
    address         text        NOT NULL
);

CREATE TABLE sponsor (
    id              serial      PRIMARY KEY,
    info_id         integer     NOT NULL REFERENCES info(id) ON DELETE CASCADE,
    name            text        NOT NULL,
    logo            text        NOT NULL,                -- URL
    rank            integer     NOT NULL DEFAULT 0,
    level           text        NOT NULL DEFAULT '',
    website         text        NOT NULL DEFAULT ''      -- URL
);

CREATE TABLE event (
    id              serial      PRIMARY KEY,
    name            text        NOT NULL,
    description     text        NOT NULL DEFAULT '',
    stream          text        NOT NULL DEFAULT 'Default',
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
        CHECK (0 < capabilities AND capabilities < 8)       -- 1: read, 2: write, 4: admin
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
    id              serial      PRIMARY KEY,               -- should only be one of these
    newsfeed        boolean     NOT NULL DEFAULT TRUE,
    events          boolean     NOT NULL DEFAULT TRUE,
    content         boolean     NOT NULL DEFAULT TRUE,
    contact         boolean     NOT NULL DEFAULT TRUE,
    location        boolean     NOT NULL DEFAULT TRUE,
    map             boolean     NOT NULL DEFAULT TRUE,
    package         boolean     NOT NULL DEFAULT TRUE,
    survey          boolean     NOT NULL DEFAULT TRUE,
    facebook        boolean     NOT NULL DEFAULT TRUE,
    twitter         boolean     NOT NULL DEFAULT TRUE,
    reposts         boolean     NOT NULL DEFAULT TRUE
);

CREATE TABLE survey (
    id              serial      PRIMARY KEY,
    name            text        NOT NULL DEFAULT '',
    description     text        NOT NULL DEFAULT '',
    link            text        NOT NULL
);

CREATE TABLE conference (
    id              serial      PRIMARY KEY,
    name            text        NOT NULL,
    url             text        NOT NULL,
    logo            text        NOT NULL DEFAULT ''
);

COMMIT;
