create table user_group (
    id integer default 0 not null,
    name varchar (100) default '',
    date_created timestamp DEFAULT (CURRENT_TIMESTAMP),
    permissions text,
    is_active integer default 1,
    primary key (id)
);

create table user (
    id integer default 0 not null,
    first_name varchar (100) default '',
    last_name varchar (100) default '',
    email varchar(255) default '',
    password varchar(255) default '',
    date_created timestamp DEFAULT (CURRENT_TIMESTAMP),
    user_group_id integer default 0 not null references user_group(id) on update cascade ,
    is_active integer default 1,
    primary key (id)
);

