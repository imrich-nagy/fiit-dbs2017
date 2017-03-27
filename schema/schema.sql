
create table account (
  id            serial primary key,
  username      varchar(30) unique not null,
  created       timestamp not null default now()
);

create table category (
  id            serial primary key,
  name          text unique not null
);

create table variety (
  id            serial primary key,
  name          text unique not null,
  category_id   integer references category not null
);

create table country (
  id            serial primary key,
  name          text unique not null
);

create table origin (
  id            serial primary key,
  name          text unique not null,
  country_id    integer references country not null
);

create table vendor (
  id            serial primary key,
  name          text unique not null,
  country_id    integer references country
);

create table tea (
  id            serial primary key,
  name          text not null,
  variety_id    integer references variety not null,
  origin_id     integer references origin,
  vendor_id     integer references vendor
);

create table purchase (
  id            serial primary key,
  purchased     date,
  active        boolean default true,
  account_id    integer references account not null,
  tea_id        integer references tea not null
);

create table flavor (
  id            serial primary key,
  name          text not null
);

create table tasting (
  id            serial primary key,
  happened      date,
  notes         text,
  account_id    integer references account not null,
  tea_id        integer references tea not null
);

create table tasting_flavor (
  tasting_id    integer references tasting,
  flavor_id     integer references flavor,
  primary key   (tasting_id, flavor_id)
);

create table review (
  id            serial primary key,
  created       timestamp not null default now(),
  notes         text not null,
  account_id    integer references account not null,
  tea_id        integer references tea not null
);

create table review_flavor (
  review_id     integer references review not null,
  flavor_id     integer references flavor not null,
  primary key   (review_id, flavor_id)
);

create table rating (
  score         integer not null check (score >= 0 and score <= 100),
  updated       timestamp not null default now(),
  account_id    integer references account not null,
  tea_id        integer references tea not null,
  primary key   (account_id, tea_id)
);
