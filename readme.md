# SuperMemo Automation (sm_auto)

This project enables remote control of SuperMemo via UI automation.

## Setup

Create a `.env` file with your credentials:

\```env
MY_APP_USERNAME={username}
MY_APP_PASSWORD={password}
\```

## Installation and Execution

Run the following commands:

\```bash
pip install -r requirements.txt
python server.py
\```

Now, your SuperMemo can be controlled remotely. You can access the web panel by opening your web browser and visiting `127.0.0.1:5000`.

If you want to access the web panel remotely, you can use tools like ngrok or host the server on a cloud platform.
