insert into main."user"
select 
uuid_generate_v3('00000000-0000-0000-0000-000000000000','01_test') as user_id,
'TEST_USER' as user_name,
'-01_test' as user_tg_code,
true as admin_flg;

insert into main."user"
select 
uuid_generate_v3('00000000-0000-0000-0000-000000000000','02_test') as user_id,
'TEST_USER' as user_name,
'-02_test' as user_tg_code,
false as admin_flg;