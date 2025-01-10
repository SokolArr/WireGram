from modules.db_api import DbManager
from modules.db_api.models import UserOrm
import logging, sys, asyncio, uuid

class User:
    pass


async def test():
    db = DbManager()
    db.create_db()
    await db.init_admins([{
            'user_tg_code': '12345', 
            'user_name': 'your_name'
        },{
            'user_tg_code': '54321', 
            'user_name': 'your_name2'
        }])
    
    
    resp = await db.add_new_user(UserOrm(user_id = uuid.uuid5(uuid.NAMESPACE_DNS, '1234567'),
                user_tg_code = '1234567', 
                user_name = 'Alex', 
                admin_flg = False))
    print(resp)
    
    resp = await db.upgrade_user('12345')
    
    print(resp.rowcount)
       
asyncio.run(test())

if __name__ == "__main__":
    logger = logging.getLogger()    
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('[%(asctime)s]-[%(name)s]-%(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    
    #console_handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)