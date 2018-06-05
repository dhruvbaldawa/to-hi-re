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


class Priorities(object):
    VERY_URGENT = 4
    URGENT = 3
    LESS_URGENT = 2
    NORMAL = 1


class Projects(object):
    TICKLER_FILE = 'Tickler File'
    ROUTINE = 'Routine'
    ROUTINE_DAILY = 'Daily'
    ROUTINE_WEEKLY = 'Weekly'
    ROUTINE_MONTHLY = 'Monthly'


class Labels(object):
    ROUTINE = 'routine'


def has_item_changed(event_name):
    return event_name in {Events.ITEM_ADDED, Events.ITEM_UPDATED}


def is_project(client, event, project_name):
    return project_name in client.projects.get_by_id(event['project_id'])['name']


def is_project_in(client, event, project_names):
    return any(is_project(client, event, project_name) for project_name in project_names)


def rule_tickler_update_text_priority(client, event_name, event):
    """ Add prefix to all tickler tasks and set their priority to very urgent """
    TICKLER_PREFIX = '!![TICKLER]!!'
    TICKLER_PRIORITY = Priorities.VERY_URGENT

    def update_content_and_priority(event):
        item = client.items.get_by_id(event['id'])
        if not item['content'].startswith(TICKLER_PREFIX):
            item.update(
                content='{prefix} {content}'.format(prefix=TICKLER_PREFIX, content=item['content']),
            )

        if item['priority'] != TICKLER_PRIORITY:
            item.update(priority=TICKLER_PRIORITY)

    return has_item_changed(event_name) \
           and is_project(client, event, Projects.TICKLER_FILE) \
           and update_content_and_priority(event)


def rule_routine_add_label(client, event_name, event):
    """ Add routine label to all the routine tasks """
    ROUTINE_PROJECTS = (
        Projects.ROUTINE,
        Projects.ROUTINE_DAILY,
        Projects.ROUTINE_WEEKLY,
        Projects.ROUTINE_MONTHLY,
    )

    def add_routine_label(event):
        item = client.items.get_by_id(event['id'])
        label_id = client.labels.all(lambda x: x['name'] == Labels.ROUTINE)[0]['id']

        if label_id not in item['labels']:
            item.update(labels=item['labels'] + [label_id, ])

    return has_item_changed(event_name) \
           and is_project_in(client, event, ROUTINE_PROJECTS) \
           and add_routine_label(event)
