import hmac
import json
import hashlib
import base64

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


def rule_label_pr_create_subtasks(client, payload):
    TASK_PREFIX = '[pr]'

    def has_prefix_pr(task):
        return task['content'].startswith(TASK_PREFIX)

    def remove_prefix_pr(task):
        task['content'] = task['content'][len(TASK_PREFIX):]
        client.items.update(task['id'], content=task['content'])
        return True

    def add_subtasks(task):
        item_offset = 0
        for content in ('Pre-requisites', 'Design', 'Implemented', 'PR', 'Merged', 'Deployed'):
            title = '{} - {}'.format(task['content'], content)
            client.add_item(content=title,
                            project_id=task['project_id'],
                            item_order=task['item_order'] + item_offset,
                            indent=task['indent'] + 1)
            item_offset += 1
        return True

    if payload['event_name'] in { Events.ITEM_ADDED, Events.ITEM_UPDATED }:
        data = payload['event_data']
        return has_prefix_pr(data) and remove_prefix_pr(data) and add_subtasks(data)


rules = (rule_label_pr_create_subtasks, )


class TodoistHandler(RequestHandler):
    def initialize(self):
        self.client = todoist.TodoistAPI(options.todoist_access_token)
        self.client.sync()

    def _verify_hmac(self, body, secret, received_signature):
        message = bytes(body).encode('utf-8')
        secret = bytes(secret).encode('utf-8')

        signature = base64.b64encode(hmac.new(secret, message, digestmod=hashlib.sha256).digest())
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
