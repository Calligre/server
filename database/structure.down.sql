BEGIN;

DROP TABLE IF EXISTS preference CASCADE;
DROP TABLE IF EXISTS broadcast CASCADE;
DROP TABLE IF EXISTS subscription CASCADE;
DROP TABLE IF EXISTS account CASCADE;
DROP TABLE IF EXISTS event CASCADE;
DROP TABLE IF EXISTS info CASCADE;

COMMIT;