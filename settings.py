import os

from tornado.options import define

define('todoist_access_token', type=str, default='')
define('todoist_client_secret', type=str)
define('todoist_client_id', type=str)
define('port', type=int, default=os.getenv('PORT', 6666), help='port to listen on')
define('debug', type=bool, default=os.getenv('DEBUG', True))

settings = {}
