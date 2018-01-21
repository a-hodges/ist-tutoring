import os
import argparse

from portal import app as application

if __name__ == '__main__':
    application.run(
        host=host,
        port=int(os.environ.get('PORT', 8000)),
        debug=False,
    )
