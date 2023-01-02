import hmac
import json
import hashlib
import base64

import requests
import tornado.log

from tornado.web import RequestHandler
from tornado.options import options

from todoist_api_python.api import TodoistAPI

from to_hi_re.rules.todoist import (
    rule_tickler_update_text_priority,
    rule_routine_add_label,
)

rules = (
    rule_tickler_update_text_priority,
    rule_routine_add_label,
)

class TodoistHandler(RequestHandler):
    def initialize(self):
        self.client = TodoistAPI(options.todoist_access_token)

    def _verify_hmac(self, body, secret, received_signature):
        received_signature = bytes(received_signature, 'utf-8')
        secret = bytes(secret, 'utf-8')
        signature = base64.b64encode(hmac.new(secret, body, digestmod=hashlib.sha256).digest())
        return signature == received_signature

    def prepare(self):
        if not self._verify_hmac(
            self.request.body,
            options.todoist_client_secret,
            self.request.headers['X-Todoist-Hmac-SHA256'],
        ):
            tornado.log.app_log.error('HMAC mismatch occured')
            self.finish()

        if self.request.headers['User-Agent'] != 'Todoist-Webhooks':
            tornado.log.app_log.error('User-Agent is not todoist')
            self.finish()

        self.json = json.loads(self.request.body)

    def post(self, *args, **kwargs):
        print(self.json)
        for rule in rules:
            rule(self.client, self.json['event_name'], self.json['event_data'])
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
