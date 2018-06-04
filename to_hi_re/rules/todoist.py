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


class Priority(object):
    VERY_URGENT = 4
    URGENT = 3
    LESS_URGENT = 2
    NORMAL = 1


class Projects(object):
    TICKLER_FILE = 'Tickler File'


def has_item_changed(event_name):
    return event_name in {Events.ITEM_ADDED, Events.ITEM_UPDATED}


def rule_tickler_update_text_priority(client, event_name, event):
    TICKLER_PREFIX = '!![TICKLER]!!'
    TICKLER_PRIORITY = Priority.VERY_URGENT

    def is_project_tickler(event):
        return Projects.TICKLER_FILE in client.projects.get_by_id(event['project_id'])['name']

    def update_content_and_priority(event):
        item = client.items.get_by_id(event['id'])

        if not item['content'].startswith(TICKLER_PREFIX):
            item.update(
                content='{prefix} {content}'.format(prefix=TICKLER_PREFIX, content=item['content']),
            )

        if item['priority'] != TICKLER_PRIORITY:
            item.update(priority=TICKLER_PRIORITY)

    return has_item_changed(event_name) and is_project_tickler(event) and update_content_and_priority(event)
