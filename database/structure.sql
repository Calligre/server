DROP TABLE IF EXISTS info CASCADE;
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
    private         boolean     NOT NULL DEFAULT FALSE
);

DROP TABLE IF EXISTS subscription CASCADE;
CREATE TABLE subscription (
    id              serial      PRIMARY KEY,
    account_id      text        NOT NULL REFERENCES account(id) ON DELETE CASCADE,
    event_id        integer     NOT NULL REFERENCES event(id) ON DELETE CASCADE
);

DROP TABLE IF EXISTS broadcast CASCADE;
CREATE TABLE broadcast (
    id              serial      PRIMARY KEY,
    message         text        NOT NULL,
    expiryTime      bigint      NOT NULL
);

DROP TABLE IF EXISTS capability CASCADE;
CREATE TABLE capability (
    id              text        PRIMARY KEY REFERENCES account(id) ON DELETE CASCADE,
    read            boolean     NOT NULL DEFAULT TRUE,
    write           boolean     NOT NULL DEFAULT FALSE,
    admin           boolean     NOT NULL DEFAULT FALSE
);

CREATE OR REPLACE FUNCTION account_capability_insert() RETURNS trigger AS
$$
BEGIN
    INSERT INTO capability(id) VALUES (NEW.id);
    RETURN NEW;
END;
$$
LANGUAGE 'plpgsql';

CREATE TRIGGER account_capability_insert_trigger AFTER INSERT ON account
    FOR EACH ROW EXECUTE PROCEDURE account_capability_insert();

CREATE OR REPLACE FUNCTION account_capability_delete() RETURNS trigger AS
$$
BEGIN
    DELETE from capability WHERE id = OLD.id;
    RETURN NEW;
END;
$$
LANGUAGE 'plpgsql';

CREATE TRIGGER account_capability_delete_trigger AFTER DELETE ON account
    FOR EACH ROW EXECUTE PROCEDURE account_capability_delete();
