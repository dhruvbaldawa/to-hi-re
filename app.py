#!/usr/bin/env python

import tornado.ioloop
import tornado.web
import tornado.options
from tornado.httpserver import HTTPServer

from to_hi_re.handlers.todoist_handler import TodoistHandler, TodoistLoginHandler


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("ping")


def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/todoist/webhook/?", TodoistHandler),
        (r"/todoist/oauth_token/?", TodoistLoginHandler),
    ], debug=True)


if __name__ == "__main__":
    app = make_app()

    server = HTTPServer(app)
    server.bind(6666)
    server.start(1)

    tornado.options.parse_config_file("settings.conf")
    tornado.ioloop.IOLoop.current().start()
