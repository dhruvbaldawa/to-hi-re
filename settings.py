import os

from tornado.options import define

define('todoist_access_token', type=str, default=os.getenv('TODOIST_ACCESS_TOKEN', ''))
define('todoist_client_secret', type=str, default=os.getenv('TODOIST_CLIENT_SECRET'))
define('todoist_client_id', type=str, default=os.getenv('TODOIST_CLIENT_ID'))
define('port', type=int, default=os.getenv('PORT', 6666), help='port to listen on')
define('debug', type=bool, default=os.getenv('DEBUG', True))

settings = {}
