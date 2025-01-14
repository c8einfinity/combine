CREATE TABLE player (
    id integer NOT NULL DEFAULT 0,
    username varchar(200) DEFAULT '',
    first_name varchar(200) DEFAULT '',
    last_name varchar(200) DEFAULT '',
    email varchar(255) DEFAULT '',
    mobile_no varchar(30) DEFAULT '',
    image blob,
    sport varchar(200),
    position varchar(200),
    home_town varchar(200) DEFAULT '',
    major varchar(200) DEFAULT '',
    date_of_birth timestamp DEFAULT (CURRENT_TIMESTAMP),
    date_created timestamp DEFAULT (CURRENT_TIMESTAMP),
    primary key (id)
);

CREATE TABLE player_result (
    id integer NOT NULL DEFAULT 0,
    data blob,
    player_id integer references player(id) on update cascade on delete cascade,
    latest integer DEFAULT 0,
    date_created timestamp DEFAULT (CURRENT_TIMESTAMP),
    primary key (id)
);

CREATE TABLE player_media (
        id integer NOT NULL DEFAULT 0,
        url varchar(1000),
        media_type varchar(100),
        player_id integer references player(id) on update cascade on delete cascade,
        is_valid integer DEFAULT 1,
        date_created timestamp DEFAULT (CURRENT_TIMESTAMP),
        primary key (id)
);

CREATE TABLE player_transcripts (
    id integer NOT NULL DEFAULT 0,
    data blob,
    player_media_id integer,
    player_id integer references player(id) on update cascade on delete cascade,
    date_created timestamp DEFAULT (CURRENT_TIMESTAMP),
    primary key (id)
);

CREATE TABLE queue (
    id integer NOT NULL DEFAULT 0,
    action varchar(100),
    data blob,
    processed integer NOT NULL DEFAULT 0,
    date_created timestamp DEFAULT (CURRENT_TIMESTAMP),
    player_id integer references player(id) on update cascade on delete cascade,
    primary key (id)
);

