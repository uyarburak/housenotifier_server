drop table if exists door_log;
create table door_log (
  id integer primary key autoincrement,
  time datetime default (datetime('now','localtime'))
);

drop table if exists ring_log;
create table ring_log (
  id integer primary key autoincrement,
  time datetime default (datetime('now','localtime'))
);

drop table if exists gas_log;
create table gas_log (
  id integer primary key autoincrement,
  time datetime default (datetime('now','localtime')),
  value real not null
);

drop table if exists phone_log;
create table phone_log (
  id integer primary key autoincrement,
  time datetime default (datetime('now','localtime')),
  is_wifi integer not null,
  device_id text not null
);