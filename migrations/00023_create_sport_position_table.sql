create table sport_position (
    id integer,
    sport_id integer not null,
    name varchar(255) not null,
    date_created timestamp not null default current_timestamp,
    date_updated timestamp not null,
    primary key (id),
    foreign key (sport_id) references sport(id)
)