import uuid
from datetime import datetime as dt
    
async def gen_uuid(input_string:str = str(dt.now()), namespace:str = 'dns'):
    '''
        Genarate UUID key for database.
        return uuid
    '''
    return str(uuid.uuid5(uuid.NAMESPACE_DNS if namespace == 'dns' else uuid.NAMESPACE_URL, input_string))