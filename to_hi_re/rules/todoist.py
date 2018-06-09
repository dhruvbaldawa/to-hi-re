import functools

import maya


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
    HOME = 'Home'
    WORK = 'Work'
    WORK_WIP = 'WIP'
    WORK_WIP_DEVOPS = 'DevOps'
    WORK_VISION = 'Vision'
    WORK_RESEARCH = 'Research'
    WORK_KOMSARY = 'Komsary'
    WORK_ICEBOX = 'Icebox'


class Labels(object):
    ROUTINE = 'routine'
    HOME = 'home'
    WORK = 'work'


def has_item_changed(event_name):
    return event_name in {Events.ITEM_ADDED, Events.ITEM_UPDATED}


def is_project(client, event, project_name):
    return project_name in client.projects.get_by_id(event['project_id'])['name']


def is_project_in(client, event, project_names):
    return any(is_project(client, event, project_name) for project_name in project_names)


def is_not_section(event):
    return not event['content'].startswith('*') and not event['content'].endswith(':')


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
           and is_not_section(event) \
           and is_project(client, event, Projects.TICKLER_FILE) \
           and update_content_and_priority(event)


def _rule_add_project_label(client, event_name, event, projects=None, label=None):
    """ Add a label to every task in given projects """
    def add_routine_label(event):
        item = client.items.get_by_id(event['id'])
        label_id = client.labels.all(lambda x: x['name'] == label)[0]['id']

        if label_id not in item['labels']:
            item.update(labels=item['labels'] + [label_id, ])

    return projects is not None \
           and label is not None \
           and has_item_changed(event_name) \
           and is_not_section(event) \
           and is_project_in(client, event, projects) \
           and add_routine_label(event)


def rule_update_timebased_priority(client, event_name, event):
    """ Update priorities of my tasks based on their timings """
    # 6AM - 12PM: orange
    # 12PM - 6PM: yellow
    MORNING_START, MORNING_END = maya.parse('06:00').datetime(), maya.parse('11:59').datetime()
    EVENING_START, EVENING_END = maya.parse('12:00').datetime(), maya.parse('18:00').datetime()

    def get_user_timezone(client):
        return client.user.get()['tz_info']['timezone']

    def has_due_date(event):
        return event['due_date_utc'] is not None

    def update_priority(client, event):
        item = client.items.get_by_id(event['id'])
        tz = get_user_timezone(client)
        local_event_time = maya.parse(event['due_date_utc']).datetime(to_timezone=tz)

        if MORNING_START.time() <= local_event_time.time() <= MORNING_END.time():
            item.update(priority=Priorities.URGENT)

        elif EVENING_START.time() <= local_event_time.time() <= EVENING_END.time():
            item.update(priority=Priorities.LESS_URGENT)

    return has_item_changed(event_name) \
           and has_item_changed(event_name) \
           and is_not_section(event) \
           and has_due_date(event) \
           and update_priority(client, event)


rule_routine_add_label = functools.partial(
    _rule_add_project_label,
    projects=(
        Projects.ROUTINE,
        Projects.ROUTINE_DAILY,
        Projects.ROUTINE_WEEKLY,
        Projects.ROUTINE_MONTHLY,
    ),
    label=Labels.ROUTINE,
)


rule_home_add_label = functools.partial(
    _rule_add_project_label,
    projects=(
        Projects.HOME,
    ),
    label=Labels.HOME,
)


rule_work_add_label = functools.partial(
    _rule_add_project_label,
    projects=(
        Projects.WORK,
        Projects.WORK_WIP,
        Projects.WORK_WIP_DEVOPS,
        Projects.WORK_VISION,
        Projects.WORK_RESEARCH,
        Projects.WORK_KOMSARY,
        Projects.WORK_ICEBOX,
    ),
    label=Labels.WORK,
)
