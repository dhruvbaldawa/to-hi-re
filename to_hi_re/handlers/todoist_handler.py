import hmac
import json
import hashlib
import base64

import requests
import tornado.log
import todoist

from tornado.web import RequestHandler
from tornado.options import options, define


define('todoist_access_token')
define('todoist_client_secret')
define('todoist_client_id')


class Events(object):
    ITEM_ADDED = 'item:added'
    ITEM_UPDATED = 'item:updated'
    ITEM_DELETED = 'item:deleted'
    ITEM_COMPLETED = 'item:completed'
    ITEM_UNCOMPLETED = 'item:uncompleted'
    NOTE_ADDED = 'note:added'
    NOTE_UPDATED = 'note:updated'
    NOTE_DELETED = 'note:deleted'
    PROJECT_ADDED = 'project:added'
    PROJECT_UPDATED = 'project:updated'
    PROJECT_DELETED = 'project:deleted'
    PROJECT_ARCHIVED = 'project:archived'
    PROJECT_UNARCHIVED = 'project:unarchived'
    LABEL_ADDED = 'label:added'
    LABEL_DELETED = 'label:deleted'
    LABEL_UPDATED = 'label:updated'
    FILTER_ADDED = 'filter:added'
    FILTER_DELETED = 'filter:deleted'
    FILTER_UPDATED = 'filter:updated'
    REMINDER_FIRED = 'reminder:fired'


rules = []


class TodoistHandler(RequestHandler):
    def initialize(self):
        self.client = todoist.TodoistAPI(options.todoist_access_token)
        self.client.sync()

    def _verify_hmac(self, body, secret, received_signature):
        received_signature = bytes(received_signature, 'utf-8')
        secret = bytes(secret, 'utf-8')
        signature = base64.b64encode(hmac.new(secret, body, digestmod=hashlib.sha256).digest())
        return signature == received_signature

    def prepare(self):
        if not self._verify_hmac(self.request.body,
                                 options.todoist_client_secret,
                                 self.request.headers['X-Todoist-Hmac-SHA256']):
            tornado.log.app_log.error('HMAC mismatch occured')
            self.finish()

        if self.request.headers['User-Agent'] != 'Todoist-Webhooks':
            tornado.log.app_log.error('User-Agent is not todoist')
            self.finish()

        self.json = json.loads(self.request.body)

    def post(self, *args, **kwargs):
        print(self.json)
        for rule in rules:
            rule(self.client, self.json)
            self.client.commit()
            self.client.sync()
        self.write('')


class TodoistLoginHandler(RequestHandler):
    TODOIST_TOKEN_API_URL = 'https://todoist.com/api/access_tokens/migrate_personal_token'

    def post(self, *args, **kwargs):
        personal_token = self.get_body_argument('personal_token')

        resp = requests.post(self.TODOIST_TOKEN_API_URL, json={
            'client_id': options.todoist_client_id,
            'client_secret': options.todoist_client_secret,
            'personal_token': personal_token,
            'scope': 'data:read_write,data:delete',
        })
        self.write(resp.json())
