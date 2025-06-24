create table admin_setting (
    id integer primary key,
    setting_key varchar(255) not null unique,
    setting_value varchar(255) not null,
    created_at timestamp default now(),
    updated_at timestamp default now()
);

insert into admin_setting (id, setting_key, setting_value) values
(1, 'video_sport_search_parameters', 'interview');

insert into admin_setting (id, setting_key, setting_value) values
    (2, 'bio_sport_search_parameters', 'full player biography');