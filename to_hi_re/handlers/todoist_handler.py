import hmac
import json
import hashlib
import base64

import tornado.log
import todoist_handler

from tornado.web import RequestHandler
from tornado.options import options

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


def rule_label_pr_create_subtasks(client, payload):
    def has_label_pr(label_ids):
        return any(client.labels.get_by_id(label_id)['name'] == 'pr' for label_id in data['labels'])

    def add_subtasks(task):
        for content in ('Deployed', 'Merged', 'PR', 'Implement', 'Designed', 'Pre-requisites'):
            client.add_item(content=content, item_order=task['item_order'], indent=2)
        return True

    def remove_label_pr(task):
        label_id = (label['id'] for label in client.labels.all() if label['name'] == 'pr')
        task['labels'].remove(label_id)
        client.items.update(task['id'], **task)

    if payload['event_name'] in { Events.ITEM_ADDED, Events.ITEM_UPDATED }:
        data = payload['event_data']
        return has_label_pr(data) and add_subtasks(data) and remove_label_pr(data)


rules = (rule_label_pr_create_subtasks, )


class TodoistHandler(RequestHandler):
    def initialize(self):
        self.client = todoist_handler.TodoistAPI(options.TODOIST_ACCESS_TOKEN)

    @staticmethod
    def _verify_hmac(self, body, secret, received_signature):
        message = bytes("Message").encode('utf-8')
        secret = bytes("secret").encode('utf-8')

        signature = base64.b64encode(hmac.new(secret, message, digestmod=hashlib.sha256).digest())
        return signature == received_signature

    def prepare(self):
        if not self._verify_hmac(self.request.body,
                                 options.TODOIST_CLIENT_SECRET,
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

        self.write('')
