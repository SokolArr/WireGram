# Documentation: Program Extension to Control Peers Using Telegram Bot (Async Version)

## Introduction

This extension allows you to manage peers using a Telegram bot. This documentation outlines the steps to set up the development environment and deploy the application in production.

## Setting Up the Development Environment

### Step 1: Create a Virtual Environment

Create a virtual environment to isolate your project's dependencies:

```
`python -m venv myenv
```

### Step 2: Activate the Virtual Environment

- **For UNIX-like systems**:
    ```
    source myenv/bin/activate
    ```

- **For Windows**:
    ```
    myenv\Scripts\activate
    ```

### Step 3: Install Dependencies

Install the required dependencies listed in the `requirements.txt` file:

```
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables

Create a `.env` file and add the necessary variables:

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

Fill in the variables with values corresponding to your configuration.

## Deployment in Production

### Step 1: Clone Repositories

Clone the necessary repositories:

```
git clone https://github.com/MHSanaei/3x-ui.git
git clone https://github.com/SokolArr/WireGram.git
```

### Step 2: Set Up and Run 3x-ui

Navigate to the `3x-ui` directory and start the containers:

```
cd 3x-ui
docker compose up -d
```

### Step 3: Set Up and Run WireGram

Go back one level and navigate to the `WireGram` directory. Make sure to configure the `docker-compose.yml` file according to your requirements:

```
cd ..
cd WireGram
```

Edit docker-compose.yml as needed.

```
docker compose up -d
```

