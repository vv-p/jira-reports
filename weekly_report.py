# -*- coding: utf-8 -*-

import jira
import settings
import jinja2
import sys
import argparse
import logging
import datetime

from main import send_on_email, get_jira_list

PREVIOUS_WEEK = 'startOfDay(-7), endOfDay(-1)'


def render(scope):
    """
    Fill Jinja2 template given values and return it as a string
    :param scope: hash with template variables and their values
    :return: rendered template as a string
    """
    jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader('templates'))
    template = jinja_env.get_template('weekly_report.html')
    return template.render(scope)


def get_weekly_issues(j, project, assignees):
    """
    Get all issues from Jira where any of testing team members marked as an assignee
    :param j: jira instance to request to
    :param project: project short-name in jira
    :param assignees: team members list
    :return: list of jira items
    """
    weekly_issues = j.search_issues(
        (
            'project = {project} AND status was Testing DURING ({period}) '  # a bit of Jira jql hacks
            'AND assignee WAS IN ({assignees}) DURING ({period}) '
        ).format(
            project=project,
            assignees=get_jira_list(assignees),
            period=PREVIOUS_WEEK,
        ),
        fields='summary',
        expand='changelog',
        maxResults=500,
    )
    return weekly_issues


def get_tested_issues(j, project, assignees):
    """
    Get all issues from Jira where any of testing team members marked as an assignee
    :param j: jira instance to request to
    :param project: project short-name in jira
    :param assignees: team members list
    :return: list of jira items
    """
    weekly_issues = j.search_issues(
        (
            'project = {project} AND status was Testing DURING ({period}) '  # a bit of Jira jql hacks
            'AND assignee WAS IN ({assignees}) DURING ({period}) '
            'AND status != Testing'
        ).format(
            project=project,
            assignees=get_jira_list(assignees),
            period=PREVIOUS_WEEK,
        ),
        fields='summary',
        expand='changelog',
        maxResults=500,
    )
    return weekly_issues


def get_state_pairs(states):
    """
    Iterate over states changing elements
    :param states: list of states
    :return:
    """
    for n in range(len(states) - 1):
        yield states[n], states[n+1]


def check_state_history(states):
    """
    Test a state changing history elements
    :param states:
    :return:
    """
    for from_state, to_state in get_state_pairs(states):
        if from_state != u'Testing':  # skip uninteresting pairs
            continue
        if to_state != u'Awaiting for deploy':  # check state changing was valid
            return False
    return True


def get_returned_issues(weekly_issues):
    """
    Get only returned to testing issues
    :param weekly_issues: all jira issues
    :return: only returned to testing issues
    """
    logger = logging.getLogger(__name__)
    returned_issues = []

    previous_week_start = datetime.datetime.now() - datetime.timedelta(days=8)
    previous_week_end = datetime.datetime.now() - datetime.timedelta(days=1)

    for issue in weekly_issues:
        states_history = []

        # Place all task states in the states_history array
        for history in issue.changelog.histories:
            for item in history.items:
                if item.field == 'status':
                    history_date = datetime.datetime.strptime(
                        history.created,
                        '%Y-%m-%dT%H:%M:%S.000+0300'
                    )

                    if previous_week_start < history_date < previous_week_end:
                        logger.debug('Add',
                                     history_date.strftime('%Y-%m-%d'),
                                     item.fromString, 'to',
                                     item.toString
                                     )
                        states_history.append(item.toString)
                    else:
                        logger.debug('Skip',
                                     history_date.strftime('%Y-%m-%d'),
                                     item.fromString,
                                     'to',
                                     item.toString)

        if not check_state_history(states_history):
            returned_issues.append(issue)

    return returned_issues


def get_closed_bugs(j, project, assignees):
    """
    Get bugs closed in last iteration
    :param j: jira instance to request to
    :param project: project short-name in jira
    :param assignees: team members list
    :return:
    """
    closed_bugs = j.search_issues(
        (
            'project = {project} '
            'AND issuetype = Bug '
            'AND status changed to Closed DURING({period}) '
            'AND assignee WAS in ({assignees})'
        ).format(
            project=project,
            assignees=get_jira_list(assignees),
            period=PREVIOUS_WEEK,
        ),
        maxResults=500,
    )
    return closed_bugs


def get_testing_issues(j, project, assignees):
    """
    :param j: jira instance to request to
    :param project: project short-name in jira
    :param assignees: team members list
    :return:
    """
    testing_issues = j.search_issues(
        (
            'project = {project} '
            'AND status = Testing '
            'AND assignee in ({assignees}) '
        ).format(
            project=project,
            assignees=get_jira_list(assignees),
        ),
        maxResults=500,
    )
    return testing_issues


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose',
                        action='store_true',
                        default=False,
                        help='be verbose')

    args = parser.parse_args()

    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=log_level)
    logger = logging.getLogger(__name__)

    smtp_auth = settings.SMTP_USER, settings.SMTP_PASS

    today = datetime.datetime.now()
    one_week_ago = today - datetime.timedelta(days=7)
    yesterday = today - datetime.timedelta(days=1)
    report_subject = settings.WEEKLY_SUBJECT.format(
        one_week_ago.strftime('%d.%m'),
        yesterday.strftime('%d.%m')
    )

    j = jira.JIRA(
        server=settings.JIRA_URL,
        basic_auth=(
            settings.JIRA_USER,
            settings.JIRA_PASS
        )
    )

    weekly_issues = get_weekly_issues(j, settings.JIRA_PROJECT, settings.FUNC)
    logger.info('Got {} weekly issues'.format(len(weekly_issues)))

    tested_issues = get_tested_issues(j, settings.JIRA_PROJECT, settings.FUNC)
    logger.info('Got {} tested issues'.format(len(tested_issues)))

    returned_issues = get_returned_issues(weekly_issues)
    logger.info('Got {} returned issues'.format(len(returned_issues)))

    closed_bugs = get_closed_bugs(j, settings.JIRA_PROJECT, settings.FUNC)
    logger.info('Got {} closed bugs'.format(len(closed_bugs)))

    testing_issues = get_testing_issues(j, settings.JIRA_PROJECT, settings.FUNC)
    logger.info('Got {} open tasks'.format(len(testing_issues)))

    scope = {
        'jira': settings.JIRA_URL,
        'weekly_issues': weekly_issues,
        'tested_issues': tested_issues,
        'returned_issues': returned_issues,
        'closed_bugs': closed_bugs,
        'testing_issues': testing_issues,
    }

    send_on_email(
        render(scope),
        report_subject,
        settings.EMAIL_FROM,
        settings.EMAIL_TO,
        smtp_auth
    )
    return 0


if __name__ == '__main__':
    sys.exit(main())
