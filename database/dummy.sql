INSERT INTO account (first_name, last_name, email, organization, photo, points,
                     facebook, twitter, linkedin, description)
    VALUES ('Clarisse', 'Schneider', 'clarissemschneider@gmail.com',
            'University of Waterloo', 'https://scontent-yyz1-1.xx.fbcdn.net/v/t1.0-1/c0.0.160.160/p160x160/13407145_10209959963904765_7384170056158382366_n.jpg?oh=10ede74cea8311ee19e790d58268db93&oe=57FD02A5',
            500, 'https://www.facebook.com/schneider.clarisse', 'https://twitter.com/claryschneider',
            'https://ca.linkedin.com/in/clarisse-schneider-03548627',
            'Im so pumped to be working at SE Hack Day! #sehackday');
INSERT INTO account (first_name, last_name, email, organization)
    VALUES ('Adam', 'Key', 'adam@google.com', 'Google');


INSERT INTO info (name, logo, location, twitter, facebook, other, startTime, endTime)
    VALUES ('SE Hackday', 'http://se.hackday.ca/assets/logo-white-0b4035ad70a69a2ffe9f254c53d11b16.png',
            'Multimedia lab', 'https://twitter.com', 'https://facebook.com',
            'Come out, do a project, and show us what ya got!', 1468120162, 1468226562);


INSERT INTO event (name, description, stream, location, startTime, endTime)
    VALUES ('Event Creation', 'This a gathering of developers working to create dummy data for displaying events',
            7, 'That one place', 1468120162, 1468120168),
           ('Test Event 2', 'This a second gathering of developers working to create dummy data for displaying events',
            7, 'That other place', 1468120172, 1468120179);


INSERT INTO subscription (account_id, event_id) VALUES (1, 1);

INSERT INTO broadcast (message, expiryTime)
    VALUES ('Hi everyone!', 1468120172),
           ('And goodbye!', 1468130172),
