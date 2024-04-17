# File: wsgi.py

from panda import app

application = app


if __name__ == "__main__":
    application.run()
