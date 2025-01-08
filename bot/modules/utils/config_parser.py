import yaml

class ConfigParser:
    def __init__(self, path_to_config: str, path_to_secret:str = ''):
        self.config_f = self.read_file(path_to_config)
        self.h_config_f = self.get_secret(path_to_secret) 
        
        try:
            self.main = self.config_f['main']
            self.bot= self.main['bot']
            self.three_xui = self.main['three_xui']
            self.logging = self.main['logging']
        except:
            raise "ERROR. BAD TRY TO READ MAIN CONFIG"
        
        try:
            self.main_h = self.h_config_f['main']
            self.bot_h = self.main_h['bot']
            self.three_xui_h = self.main_h['three_xui']
            self.logging_h = self.main_h['logging']
        except Exception as e:
            print(e)
        
    def get_bot_config(self) -> dict:
        if self.bot['token']:
            return self.bot
        else:
            try:
                return self.bot_h
            except:
                raise "NO BOT CONFIG"
            
    def get_three_xui_config(self) -> dict:
        if self.three_xui['host_url']:
            return self.three_xui
        else:
            try:
                return self.three_xui_h
            except:
                raise "NO 3X UI CONFIG"
            
    def get_logging_config(self) -> dict:
        if self.logging:
            return self.logging
        else:
            try:
                return self.logging_h
            except:
                raise "NO BOT CONFIG"
    
    @staticmethod
    def read_file(file_path: str) -> dict:
        with open(file_path, 'r') as file:
            data:dict = yaml.safe_load(file)
        return data
    
    def get_secret(self, path:str) -> dict:
        data = {}
        try: 
            data = self.read_file(path)
        except Exception as e: 
          print(e)  
        finally:
            return data