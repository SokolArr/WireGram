create extension if not exists "uuid-ossp";

-->> SCHEMA <<------------------------------------------------------------------------------------------------------
drop schema if exists main cascade;
create schema if not exists main;

drop schema if exists logs cascade;
create schema if not exists logs;

-->> TABLES <<------------------------------------------------------------------------------------------------------
drop table if exists main."user" cascade;
create table if not exists main."user" (
	user_id uuid primary key,
	user_name text default 'NO_USER_NAME',
	user_tg_code text not null,
	admin_flg boolean default false,
	--tech_attrs
	sys_inserted_process text default 'MANUAL' not null,
	sys_inserted_dttm timestamp default current_timestamp not null
);

drop table if exists main.user_vpn_access cascade;
create table if not exists main.user_vpn_access (
	user_id uuid not null,
	access_from_dttm timestamp default current_timestamp not null,
	access_to_dttm timestamp default '9999-01-01'::date not null,
	--tech_attrs
	sys_inserted_process text default 'MANUAL' not null,
	sys_inserted_dttm timestamp default current_timestamp not null
);

drop table if exists main.user_bot_access cascade;
create table if not exists main.user_bot_access (
	user_id uuid not null,
	access_from_dttm timestamp default current_timestamp not null,
	access_to_dttm timestamp default '9999-01-01'::date not null,
	--tech_attrs
	sys_inserted_process text default 'MANUAL' not null,
	sys_inserted_dttm timestamp default current_timestamp not null
);

drop table if exists main.user_req_access cascade;
create table if not exists main.user_req_access (
	user_tg_code text not null primary key,
	user_name text default 'NO_USER_NAME',
	--tech_attrs
	sys_inserted_dttm timestamp default current_timestamp not null
);

drop table if exists main.user_order cascade;
create table if not exists main.user_order (
	user_id uuid,
	order_id uuid,
	--tech_attrs
	sys_inserted_process text default 'MANUAL' not null,
	sys_inserted_dttm timestamp default current_timestamp not null,
	--constraints
	constraint user_order_pk primary key (user_id, order_id)
);

drop table if exists main.user_vpn_price cascade;
create table if not exists main.user_vpn_price (
	user_id uuid,
	price decimal,
	effective_from_dt date not null,
	effective_to_dt date not null,
	--tech_attrs
	sys_inserted_process text default 'MANUAL' not null,
	sys_inserted_dttm timestamp default current_timestamp not null,
	--constraints
	constraint user_vpn_price_pk primary key (user_id, effective_from_dt)
);

drop table if exists main.user_notif_param cascade;
create table if not exists main.user_notif_param (
	notif_id int,
	notif_name text,
	user_id uuid,
	nitif_per_mnth_cnt int4,
	notif_3d_before_dttm timestamp,
	notif_1d_before_dttm timestamp,
	notif_dttm timestamp,
	--tech_attrs
	sys_inserted_process text default 'MANUAL' not null,
	sys_inserted_dttm timestamp default current_timestamp not null,
	--constraints
	constraint user_notif_param_pk primary key (notif_id, user_id)
);

drop table if exists main."order" cascade;
create table if not exists main."order" (
	order_id uuid primary key,
	order_amnt decimal,
	order_dttm timestamp,
	--tech_attrs
	sys_inserted_process text default 'MANUAL' not null,
	sys_inserted_dttm timestamp default current_timestamp not null
);

drop table if exists main.vpn_param cascade;
create table if not exists main.vpn_param (
	vpn_name text,
	server_name text,
	server_link_http text,
	server_access_from_dttm timestamp,
	server_access_to_dttm timestamp,
	--tech_attrs
	sys_inserted_process text default 'MANUAL' not null,
	sys_inserted_dttm timestamp default current_timestamp not null,
	--constraints
	constraint vpn_param_pk primary key (vpn_name, server_name)
);

-->> VIEWS <<----------------------------------------------------------------------------------------------------
drop view if exists main.v_user_x_user_access;
create or replace view main.v_user_x_user_access as
select 
	"user".user_id,
	"user".user_name,
	"user".user_tg_code,
	"user".admin_flg,
	user_bot_access.access_from_dttm as bot_access_from_dttm,
	user_bot_access.access_to_dttm as bot_access_to_dttm,
	user_vpn_access.access_from_dttm as vpn_access_from_dttm,
	user_vpn_access.access_to_dttm as vpn_access_to_dttm
from 
	main.user
join
	main.user_bot_access
using(user_id)
left join
	main.user_vpn_access
using(user_id);

drop view if exists main.v_new_user;
create or replace view main.v_new_user as
select 
	user_tg_code,
	user_name,
	--tech_attrs
	sys_inserted_dttm
from
	main.user_req_access
where 
	user_tg_code not in (select user_tg_code from main.v_user_x_user_access);