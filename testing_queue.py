# -*- coding: utf-8 -*-

import settings
import jira
import jinja2
import datetime
import sys
import collections
import argparse

from main import send_on_email, get_jira_list


def get_critical_tasks(j, project, assignees):
    assignees = get_jira_list(assignees)

    critical_tasks = j.search_issues(
        (
            f'project = {project} '
            f'AND Status = Testing '
            f'AND assignee IN ({assignees}) '
            f'AND priority = Критический '
        ),
        maxResults=500,
        fields='summary,assignee,reporter',
    )
    return critical_tasks


def get_bugs(j, project, assignees):
    who = get_jira_list(assignees)

    bugs = j.search_issues(
        (
            f'project = {project} '
            f'AND issuetype = Bug '
            f'AND assignee IN ({who}) '
            f'AND status = Testing '
        ),
        maxResults=500,
        fields='summary,assignee,reporter',
    )
    return bugs


def get_old_tasks(j, project, assignees, max_age, max_results):
    """
    Search in jira tasks with a big testing timeout
    :param j: Jira instance
    :param project: Jira project name
    :param assignees: team members list
    :param max_age: maximum testing timeout value in days
    :param max_results: maximum number of tasks returned
    :return: list of jira tasks
    """
    who = get_jira_list(assignees)

    old_tasks = j.search_issues(
        (
            f'project = {project} '
            f'AND status = Testing '
            f'AND assignee IN ({who}) '
            f'AND status CHANGED TO Testing BEFORE -{max_age}d '
        ),
        maxResults=500,
        fields='summary,assignee,reporter',
        expand='changelog',
    )

    def sort_key(issue):
        for histories in issue.changelog.histories[::-1]:
            for history in histories.items:
                if history.toString == 'Testing':
                    return histories.created
        return datetime.datetime.now()

    return sorted(old_tasks, key=sort_key)[:max_results]


def render(scope):
    """
    Fill Jinja2 template given values and return it as a string
    :param scope: hash with template variables and their values
    :return: rendered template as a string
    """
    jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader('templates'))

    template = jinja_env.get_template('testing_queue.html')
    return template.render(scope)


def key(n):
    """
    Get task key from the task number, for example: 22343 -> TRG-22343
    :param n: int, task number
    :return: str, task key
    """
    return f'TRG-{n}'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--max-age', required=True, type=int, help='maximum task age (days)')
    parser.add_argument('-p', '--push', required=False, type=int, nargs='+', help='Push this tasks to the queue',
                        default=())
    parser.add_argument('-s', '--skip', required=False, type=int, nargs='+', help='Skip this tasks in the queue',
                        default=())
    parser.add_argument('-q', '--max-queue', required=False, type=int, help='maximum queue size', default=50)
    args = parser.parse_args()

    skip = [key(n) for n in args.skip]

    j = jira.JIRA(
        server=settings.JIRA_URL,
        basic_auth=(
            settings.JIRA_USER,
            settings.JIRA_PASS)
    )

    tasks = collections.OrderedDict()

    critical = get_critical_tasks(j, settings.JIRA_PROJECT, settings.FUNC)
    bugs = get_bugs(j, settings.JIRA_PROJECT, settings.FUNC)

    max_queue = args.max_queue
    old_count = max_queue - len(critical) - len(bugs) - len(args.push)

    old = get_old_tasks(j, settings.JIRA_PROJECT, settings.FUNC, args.max_age, old_count)

    for suite in critical, bugs, old:
        for task in suite:
            if task.key in skip:
                continue
            tasks[task.key] = task

    for i in args.push:
        task_key = key(i)
        try:
            tasks[task_key] = j.issue(task_key)
        except jira.exceptions.JIRAError:
            pass

    scope = {
        'tasks': tasks,
        'max_age': args.max_age,
    }

    smtp_auth = settings.SMTP_USER, settings.SMTP_PASS

    send_on_email(
        render(scope),
        settings.QUEUE_SUBJECT.format(datetime.datetime.now().strftime('%d-%m-%Y')),
        settings.EMAIL_FROM,
        settings.EMAIL_TO,
        smtp_auth
    )
    return 0


if __name__ == '__main__':
    sys.exit(main())
