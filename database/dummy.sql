BEGIN;

INSERT INTO account (id, first_name, last_name, email, organization, photo,
                     points, facebook, twitter, linkedin, description, capabilities)
    VALUES ('1', 'Clarisse', 'Schneider', 'clarissemschneider@gmail.com',
            'University of Waterloo', 'https://scontent-yyz1-1.xx.fbcdn.net/v/t1.0-1/c0.0.160.160/p160x160/13407145_10209959963904765_7384170056158382366_n.jpg?oh=10ede74cea8311ee19e790d58268db93&oe=57FD02A5',
            500, 'https://www.facebook.com/schneider.clarisse', 'https://twitter.com/claryschneider',
            'https://ca.linkedin.com/in/clarisse-schneider-03548627',
            'Im so pumped to be working at SE Hack Day! #sehackday', 7);
INSERT INTO account (id, first_name, last_name, email, organization, capabilities)
    VALUES ('2', 'Adam', 'Key', 'adam@google.com', 'Google', 3),
           ('adsku43oufo4ulf', 'Kadam', 'Ey', 'kadam@google.com', 'KGoogle', 1);


INSERT INTO info (id, name, organization, logo, twitter, facebook, startTime, endTime)
    VALUES (1, 'SE Hackday', 'Anonymoose', 'https://static1.squarespace.com/static/5141f98de4b01238136e109c/t/55cce2d9e4b00c260f1f40e4/1439490779089/librato-hack-day',
            'https://twitter.com', 'https://facebook.com', 1468120162, 1468226562);
INSERT INTO card (info_id, data)
    VALUES (1, 'Come out, do a project, and show us what ya got!');
INSERT INTO contact (info_id, name, phone)
    VALUES (1, 'Jenny', '867-5309');
INSERT INTO location (info_id, name, address)
    VALUES (1, 'Home Base', 'Multimedia Lab'),
           (1, 'Workshops', 'SE Lounge');


INSERT INTO event (name, description, stream, location, startTime, endTime)
    VALUES ('Event Creation', 'This a gathering of developers working to create dummy data for displaying events', 'workshops', 'That one place', 1468162800, 1468166400),
           ('Tomorrow', 'This event happens tomorrow', 'workshops', 'That one place', 1468249740, 1468253340),
           ('Yesterday', 'This event happened yesterday', 'workshops', 'That one place', 1468076940, 1468080540),
           ('All Day', 'This event lasts all day', 'workshops', 'That one place', 1468162800, 1468195200),
           ('Broken', 'This event is broken', 'workshops', 'That one place', 1468195200, 1468162800),
           ('Another Stream,', 'This event is in another stream', 'food', 'That one place', 1468162800, 1468166400),
           ('No Description', '', 'workshops', 'That one place', 1468162800, 1468166400);


INSERT INTO preference (id) VALUES (1);


INSERT INTO subscription (account_id, event_id) VALUES ('1', 1);


INSERT INTO broadcast (message, expiryTime)
    VALUES ('Hi everyone!', 1468120172),
           ('And goodbye!', 1468130172),
           ('This broadcast is from 2016!', 1478217600),
           ('This is from 2017!', 1509753600);

COMMIT;
