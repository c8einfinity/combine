create table admin_settings (
    id integer primary key,
    setting_key varchar(255) not null unique,
    setting_value varchar(255) not null,
    created_at timestamp default now(),
    updated_at timestamp default now()
);