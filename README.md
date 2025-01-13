## Program-extension to control peers using telegram bot (async version)

```python -m venv myenv```
```source myenv/bin/activate``` or ```myenv\Scripts\activate```

```pip install -r r.txt```

```
cat <<EOL > .env
DEBUG_MODE = True
WRITE_LOGS = True

BOT_TOKEN = ""
TG_ADMIN_ID = ""

DB_HOST = ""
DB_PORT = 
DB_USER = ""
DB_PASS = ""
DB_NAME = ""

XUI_HOST = ""
XUI_USER = ""
XUI_PASS = ""
EOL
```

git clone https://github.com/MHSanaei/3x-ui.git
git clone https://github.com/SokolArr/WireGram.git
cd 3x-ui

docker compose up -d