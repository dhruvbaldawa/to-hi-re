import tornado.ioloop
import tornado.web
from to_hi_re.handlers.todoist import TodoistHandler

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("ping")


def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/webhooks/todoist", TodoistHandler)
    ])

if __name__ == "__main__":
    app = make_app()
    app.listen(6666)
    tornado.ioloop.IOLoop.current().start()