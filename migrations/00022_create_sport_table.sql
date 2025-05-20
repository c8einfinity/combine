create table sport (
    id integer,
    name varchar(255) not null,
    date_created timestamp not null default current_timestamp,
    date_updated timestamp not null,
    primary key (id)
)