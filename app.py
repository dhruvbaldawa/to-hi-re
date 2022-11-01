#!/usr/bin/env python

from settings import settings

import tornado.ioloop
import tornado.web
from tornado.options import options
from tornado.httpserver import HTTPServer
from tornado.log import enable_pretty_logging

from to_hi_re.handlers.todoist_handler import TodoistHandler, TodoistLoginHandler


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("ping")


def make_app(settings):
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/todoist/webhook/?", TodoistHandler),
        (r"/todoist/oauth_token/?", TodoistLoginHandler),
    ], **settings)


if __name__ == "__main__":
    enable_pretty_logging()
    app = make_app(settings)

    server = HTTPServer(app)
    server.bind(options.port)
    server.start(1)

    tornado.ioloop.IOLoop.current().start()
