import uvicorn as uvicorn

from app.main import app

# Don't forget to import the config var with a correct path to the debug config.
# e.g. for intellij debugger env DEBUGGING_CONFIG=./debug.env

uvicorn.run(app, host="0.0.0.0", port=8000)
