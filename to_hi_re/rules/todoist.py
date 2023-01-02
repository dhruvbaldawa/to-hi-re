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
    HOME_3710 = '3710'
    WORK = 'Work'
    WORK_WIP = 'WIP'
    WORK_WIP_DEVOPS = 'DevOps'
    WORK_VISION = 'Vision'
    WORK_RESEARCH = 'Research'
    WORK_KOMSARY = 'Komsary'
    WORK_ICEBOX = 'Icebox'
    WORK_NOTES = 'Notes'
    GOALS = 'Goals'
    GOALS_LONG_TERM = 'Long term'
    GOALS_LEARNING = 'Learning'
    GOALS_TRAVEL = 'Travel'
    GOALS_BRAND = 'Brand'
    GOALS_FIT = 'Fit'


class Labels(object):
    ROUTINE = 'routine'
    HOME = 'home'
    WORK = 'work'
    GOALS = 'goal'


def has_item_changed(event_name):
    return event_name in {Events.ITEM_ADDED, Events.ITEM_UPDATED}


def is_project(client, event, project_name):
    return project_name in client.get_project(project_id=event['project_id']).name


def is_project_in(client, event, project_names):
    return any(is_project(client, event, project_name) for project_name in project_names)


def is_not_section(event):
    return not event['content'].startswith('*') and not event['content'].endswith(':')


def rule_tickler_update_text_priority(client, event_name, event):
    """ Add prefix to all tickler tasks and set their priority to very urgent """
    TICKLER_PREFIX = '**[TICKLER]**'
    TICKLER_PRIORITY = Priorities.VERY_URGENT

    def update_content_and_priority(event):
        item = client.get_task(task_id=event['id'])
        if not item.content.startswith(TICKLER_PREFIX):
            client.update_task(
                task_id=event['id'],
                content='{prefix} {content}'.format(prefix=TICKLER_PREFIX, content=item.content),
            )

        if item.priority != TICKLER_PRIORITY:
            client.update_task(
                task_id=event['id'],
                priority=TICKLER_PRIORITY,
            )

    return has_item_changed(event_name) \
        and is_not_section(event) \
        and is_project(client, event, Projects.TICKLER_FILE) \
        and update_content_and_priority(event)


def _rule_add_project_label(client, event_name, event, projects=None, label=None):
    """ Add a label to every task in given projects """
    def add_label(event):
        item = client.get_task(task_id=event['id'])

        if label not in item.labels:
            client.update_task(task_id=event['id'], labels=item.labels + [label, ])

    return projects is not None \
        and label is not None \
        and has_item_changed(event_name) \
        and is_not_section(event) \
        and is_project_in(client, event, projects) \
        and add_label(event)


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
        Projects.HOME_3710,
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
        Projects.WORK_NOTES,
    ),
    label=Labels.WORK,
)


rule_goals_add_label = functools.partial(
    _rule_add_project_label,
    projects=(
        Projects.GOALS,
        Projects.GOALS_LONG_TERM,
        Projects.GOALS_LEARNING,
        Projects.GOALS_TRAVEL,
        Projects.GOALS_BRAND,
        Projects.GOALS_FIT,
    ),
    label=Labels.GOALS,
)
