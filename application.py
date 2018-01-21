import os

from portal import app as application

if __name__ == '__main__':
    application.run(
        host='127.0.0.1',
        port=int(os.environ.get('PORT', 8000)),
        debug=False,
    )
