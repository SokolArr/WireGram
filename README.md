### Wiregram Project Description 🌟

**Wiregram** is a project for managing **vless** configurations (via **3x-ui**) using a Telegram bot. 🚀 The project provides an out-of-the-box solution for automating configuration management, notifications, and logging. Everything you need to get started is included in the **docker-compose** file. You just need to fill in the configuration and launch the project. 🛠️

#### Key Features: ✨
- Manage **vless** configurations via a Telegram bot. 🤖
- Automatic logging and notifications. 📨
- Ready-to-use **docker-compose** file for quick deployment. 🐳
- **PostgreSQL** database for data storage. 🗄️
- Flexible configuration via environment variables. ⚙️

#### Getting Started: 🚀
1. Fill in the `docker-compose.yml` file with your data (bot token, database settings, etc.). 📝
2. Start the project with the command:
   ```bash
   docker-compose up -d
   ```
3. That's it! 🎉 Your bot and database will be up and running, ready to use. ✅

---

### Detailed Description of `docker-compose.yml` 📄

This file describes the configuration for running several services:
1. **Telegram Bot** — the main service for managing configurations. 🤖
2. **Notifyer** — a service for sending notifications. 📨
3. **PostgreSQL Database** — the database for storing information. 🗄️

#### 1. **Service `telegram_bot`**
- **build**: Builds the image from the Dockerfile in the `./src` directory. 🛠️
- **volumes**: Bot logs are saved to the `./bot_logs` directory on the host. 📂
- **environment**: Bot settings, database configurations, administrative parameters, and app links. ⚙️
- **depends_on**: Depends on the `db` service (database). 🔗
- **restart: always**: Automatically restarts in case of failures. 🔄

#### 2. **Service `notifyer`**
- **build**: Builds the image from the Dockerfile in the `./src/notifyer` directory. 🛠️
- **volumes**: Notifier logs are saved to the `./notifyer_logs` directory on the host. 📂
- **depends_on**: Depends on the `telegram_bot` service. 🔗
- **restart: always**: Automatically restarts in case of failures. 🔄

#### 3. **Service `db`**
- **image**: Uses the official PostgreSQL image (version 14). 🐘
- **environment**: Database settings (user, password, timezone, etc.). ⚙️
- **ports**: Port 5432 of the container is mapped to port 5430 on the host. 🔌
- **volumes**: Database data is saved to the `./db_data` directory on the host. 📂
- **healthcheck**: Checks the database status every 30 seconds. ⏱️
- **restart: unless-stopped**: Restarts the container unless it was stopped manually. 🔄

---

### Description of `environment` Parameters in `docker-compose.yml` 🛠️

This section describes all the environment variables used to configure the services. Let's break down each one:

---

#### **1. Project (Project Settings)** 🏗️
- **DEBUG_MODE**: Enables or disables debug mode.  
  - **Value**: `true` (enabled) or `false` (disabled).  
  - **Example**: `DEBUG_MODE: true`  

- **WRITE_LOGS**: Determines whether logs will be written to a file.  
  - **Value**: `true` (logs are written) or `false` (logs are not written).  
  - **Example**: `WRITE_LOGS: true`  

- **DEFAULT_TIMEZONE**: Sets the timezone for the services.  
  - **Value**: Timezone name (e.g., `Europe/Moscow`).  
  - **Example**: `DEFAULT_TIMEZONE: Europe/Moscow`  

---

#### **2. TG bot (Telegram Bot Settings)** 🤖
- **BOT_TOKEN**: The token for your Telegram bot, obtained from [BotFather](https://core.telegram.org/bots#botfather).  
  - **Value**: A string containing the token.  
  - **Example**: `BOT_TOKEN: 123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`  

- **TG_ADMIN_ID**: The ID of the bot administrator. Used for access management.  
  - **Value**: Numeric Telegram user ID.  
  - **Example**: `TG_ADMIN_ID: 123456789`  

---

#### **3. Database (Database Settings)** 🗄️
- **DB_HOST**: The database host.  
  - **Value**: The name of the database service (in this case, `db`).  
  - **Example**: `DB_HOST: db`  

- **DB_PORT**: The database port.  
  - **Value**: Port number (default for PostgreSQL is `5432`).  
  - **Example**: `DB_PORT: 5432`  

- **DB_USER**: The database username.  
  - **Value**: A string containing the username.  
  - **Example**: `DB_USER: admin`  

- **DB_PASS**: The database user's password.  
  - **Value**: A string containing the password.  
  - **Example**: `DB_PASS: admin`  

- **DB_NAME**: The database name.  
  - **Value**: A string containing the database name.  
  - **Example**: `DB_NAME: db`  

---

#### **4. Database main user (Main Database User)** 👤
- **DB_WG_USER**: The username for working with the database (e.g., for managing configurations).  
  - **Value**: A string containing the username.  
  - **Example**: `DB_WG_USER: wg`  

- **DB_WG_PASS**: The password for the `DB_WG_USER`.  
  - **Value**: A string containing the password.  
  - **Example**: `DB_WG_PASS: wg`  

---

#### **5. Database root schema (Root Database Schema)** 📂
- **DB_DEFAULT_SCHEMA_NAME**: The name of the root database schema.  
  - **Value**: A string containing the schema name.  
  - **Example**: `DB_DEFAULT_SCHEMA_NAME: wg`  

---

#### **6. 3x-ui (3x-ui Settings)** 🌐
- **XUI_HOST**: The host for connecting to 3x-ui.  
  - **Value**: URL or IP address.  
  - **Example**: `XUI_HOST: http://example.com`  

- **XUI_USER**: The username for accessing 3x-ui.  
  - **Value**: A string containing the username.  
  - **Example**: `XUI_USER: admin`  

- **XUI_PASS**: The password for accessing 3x-ui.  
  - **Value**: A string containing the password.  
  - **Example**: `XUI_PASS: admin`  

- **XUI_VLESS_PORT**: The port for working with VLESS configurations.  
  - **Value**: Port number.  
  - **Example**: `XUI_VLESS_PORT: 4000`  

- **XUI_MAX_USED_PORTS**: The maximum number of used ports.  
  - **Value**: Numeric value.  
  - **Example**: `XUI_MAX_USED_PORTS: 1000`  

---

#### **7. Administration (Administrative Settings)** ⚙️
- **BOT_ACCESS_EXPIRED_DELTA_DAYS**: The validity period of bot access (in days).  
  - **Value**: Number of days.  
  - **Example**: `BOT_ACCESS_EXPIRED_DELTA_DAYS: 365`  

- **CONF_PAY_EXPIRED_DELTA_DAYS**: The validity period of a paid configuration (in days).  
  - **Value**: Number of days.  
  - **Example**: `CONF_PAY_EXPIRED_DELTA_DAYS: 30`  

- **FREE_CONF_PERIOD_DAYS**: The validity period of a free configuration (in days).  
  - **Value**: Number of days.  
  - **Example**: `FREE_CONF_PERIOD_DAYS: 7`  

- **MAX_CONF_PER_USER**: The maximum number of configurations per user.  
  - **Value**: Numeric value.  
  - **Example**: `MAX_CONF_PER_USER: 2`  

- **TG_HELP_CHAT_LINK**: The link to the Telegram support chat.  
  - **Value**: URL link.  
  - **Example**: `TG_HELP_CHAT_LINK: https://t.me/your_help_chat`  

---

#### **8. Vless app links (Links to VLESS Applications)** 📲
- **VLESS_APP_ANDROID_LINK**: The link to the Android app.  
  - **Value**: URL link.  
  - **Example**: `VLESS_APP_ANDROID_LINK: https://play.google.com/store/apps/details?id=com.v2raytun.android`  

- **VLESS_APP_APPLE_LINK**: The link to the iOS app.  
  - **Value**: URL link.  
  - **Example**: `VLESS_APP_APPLE_LINK: https://apps.apple.com/app/id6476628951`  

- **VLESS_APP_PC_LINK**: The link to the PC app.  
  - **Value**: URL link.  
  - **Example**: `VLESS_APP_PC_LINK: https://github.com/2dust/v2rayN/releases/`  

- **VLESS_APP_ALL_LINK**: A general link to apps for all platforms.  
  - **Value**: URL link.  
  - **Example**: `VLESS_APP_ALL_LINK: https://vlesskey.com/download`  

---

### Example of Filling in All Parameters: 📝

```yaml
environment:
  # Project:
  DEBUG_MODE: true
  WRITE_LOGS: true
  DEFAULT_TIMEZONE: Europe/Moscow

  # TG bot:
  BOT_TOKEN: 123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
  TG_ADMIN_ID: 123456789

  # Database:
  DB_HOST: db
  DB_PORT: 5432
  DB_USER: admin
  DB_PASS: admin
  DB_NAME: db

  # Database main user:
  DB_WG_USER: wg
  DB_WG_PASS: wg

  # Database root schema:
  DB_DEFAULT_SCHEMA_NAME: wg

  # 3x-ui:
  XUI_HOST: http://example.com
  XUI_USER: admin
  XUI_PASS: admin
  XUI_VLESS_PORT: 4000
  XUI_MAX_USED_PORTS: 1000

  # Administration:
  BOT_ACCESS_EXPIRED_DELTA_DAYS: 365
  CONF_PAY_EXPIRED_DELTA_DAYS: 30
  FREE_CONF_PERIOD_DAYS: 7
  MAX_CONF_PER_USER: 2
  TG_HELP_CHAT_LINK: https://t.me/your_help_chat

  # Vless app links:
  VLESS_APP_ANDROID_LINK: https://play.google.com/store/apps/details?id=com.v2raytun.android
  VLESS_APP_APPLE_LINK: https://apps.apple.com/app/id6476628951
  VLESS_APP_PC_LINK: https://github.com/2dust/v2rayN/releases/
  VLESS_APP_ALL_LINK: https://vlesskey.com/download
```