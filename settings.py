# coding: utf-8

import os.path
import yaml
import logging


CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'settings.yaml')

logger = logging.getLogger(__name__)


try:
    with open(CONFIG_PATH, 'r') as fh:
        config = yaml.load(fh)
except FileNotFoundError:
    logging.error('Config file was not found: settings.yaml')
    logging.error('You must create it first')
    exit(1)

# Jira settings
JIRA_URL = config['jira']['url']
JIRA_USER = config['jira']['user']
JIRA_PASS = config['jira']['pass']
JIRA_PROJECT = config['jira']['project']

# SMTP settings
SMTP_HOST = config['smtp']['host']
SMTP_PORT = config['smtp']['port']
SMTP_USER = config['smtp']['user']
SMTP_PASS = config['smtp']['pass']

# Mail settings
EMAIL_FROM = config['email']['from']
EMAIL_TO = config['email']['to']
DAILY_SUBJECT = config['email']['daily_subject']
QUEUE_SUBJECT = config['email']['queue_subject']
AGES_SUBJECT = config['email']['ages_subject']
WEEKLY_SUBJECT = config['email']['weekly_subject']

# Team settings
TEAM = [x['mail'] for x in config['team']]
FUNC = [x['mail'] for x in config['team'] if x['role'] == 'manual']
AUTO = [x['mail'] for x in config['team'] if x['role'] == 'auto']
