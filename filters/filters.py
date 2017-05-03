import re
import os


def get_emoji_content(filename):
    full_filename = os.path.join(os.path.dirname(__file__), 'emojis', filename)
    with open(full_filename, 'r') as fp:
        return fp.read()


def fix_emoji(value):
    """
    Replace some text emojis with pictures
    """
    emojis = {
        '(+)': get_emoji_content('plus.html'),
        '(-)': get_emoji_content('minus.html'),
        '(?)': get_emoji_content('question.html'),
        '(!)': get_emoji_content('alarm.html'),
        '(/)': get_emoji_content('check.html'),
    }
    for e in emojis:
        value = value.replace(e, emojis[e])
    return value


def cleanup(value):
    """
    Remove {code}...{/code} and {noformat}...{noformat} fragments from worklog comment
    :param value: worklog comment text
    :return: cleaned worklog comment text
    """
    value = re.sub('\{code.*?\}.*?\{.*?code\}', ' ', value, 0, re.S)
    return re.sub('\{noformat.*?\}.*?\{noformat\}', ' ', value, 0, re.S)
