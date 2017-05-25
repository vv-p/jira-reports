# -*- coding: utf-8 -*-

import jira
import jinja2
import sys
import argparse
import logging
import datetime
import collections
import settings

from main import send_on_email, get_day_offset
from filters import cleanup, fix_emoji


def get_issues(j, project, date, authors):
    """
    Get tasks from jira
    :param j: jira instance
    :param project: project short-name in jira
    :param date: filter by date
    :param authors: filter by authors
    :return: tasks list
    """

    issues = j.search_issues(
        (
            'project = {project} '
            'AND worklogDate = {date:%Y-%m-%d} '
            'AND timespent > 0 '
            'AND worklogAuthor IN ({authors})'
        ).format(
            project=project,
            date=date,
            authors=', '.join('"%s"' % x for x in authors),
        ),
        fields='summary,worklog',
        maxResults=settings.MAX_RESULTS,
    )
    return issues


def parse_worklogs(j, date, authors, issues):
    total = 0  # Total counter
    logger = logging.getLogger(__name__)

    report = collections.defaultdict(list)

    for issue in issues:
        for worklog in j.worklogs(issue):
            if worklog.updateAuthor.name not in authors:
                logger.debug('Skip worklog in {issue.key} by {author}'.format(
                    issue=issue,
                    author=worklog.updateAuthor.name)
                )
                continue

            worklog_date = datetime.datetime.strptime(
                worklog.started,
                '%Y-%m-%dT%H:%M:%S.000+0300'
            )

            if worklog_date.date() != date:
                logger.debug('Skip worklog in {issue.key}, it has started date = {date:%d-%m-%Y}'.format(
                    issue=issue,
                    date=worklog_date))
                continue

            logger.debug('Add worklog from {issue.key} by {author} for {date:%d-%m-%Y}'.format(
                issue=issue,
                author=worklog.updateAuthor.name,
                date=worklog_date)
            )

            report[worklog.updateAuthor.displayName].append((
                issue.key,
                issue.fields.summary,
                worklog.timeSpent,
                worklog.comment,
            ))
            total += 1

    return report, total


def render(scope):
    """
    Fill Jinja2 template given values and return it as a string
    :param scope: hash with template variables and their values
    :return: rendered template as a string
    """
    jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader('templates'))

    # Install custom Jinja2 filters
    jinja_env.filters['cleanup'] = cleanup
    jinja_env.filters['fix_emoji'] = fix_emoji

    template = jinja_env.get_template('daily_report.html')
    return template.render(scope)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose',
                        action='store_true',
                        default=False,
                        help='be verbose')
    args = parser.parse_args()

    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=log_level)

    smtp_auth = settings.SMTP_USER, settings.SMTP_PASS

    j = jira.JIRA(
        server=settings.JIRA_URL,
        basic_auth=(
            settings.JIRA_USER,
            settings.JIRA_PASS)
    )

    date = datetime.date.today() - datetime.timedelta(days=get_day_offset())

    report_subject = settings.DAILY_SUBJECT.format(
        date.strftime('%Y-%m-%d'),
    )

    issues = get_issues(j, settings.JIRA_PROJECT, date, settings.FUNC)

    report, total = parse_worklogs(j, date, settings.FUNC, issues)
    scope = {
        'report': report,
        'total': total,
    }
    send_on_email(
        render(scope),
        report_subject,
        settings.EMAIL_FROM,
        settings.EMAIL_TO,
        smtp_auth
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
