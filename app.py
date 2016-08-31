import tornado.ioloop
import tornado.web
import tornado.options

from to_hi_re.handlers.todoist_handler import TodoistHandler


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("ping")


def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/webhooks/todoist", TodoistHandler)
    ], debug=True)


if __name__ == "__main__":
    app = make_app()
    app.listen(6666)
    tornado.options.parse_config_file("settings.conf")
    tornado.ioloop.IOLoop.current().start()