#!/usr/bin/python3
# -*- coding: utf-8 -*-

import re
import os

from mattermost_bot.bot import respond_to
from jira import JIRA

JIRA_URL = os.environ.get("MATTERBOT_JIRA_URL")
PROJECT = os.environ.get("MATTERBOT_JIRA_PROJECT")
JIRA_CONNECTOR = JIRA(JIRA_URL, basic_auth=(
    os.environ.get("MATTERBOT_JIRA_LOGIN"),
    os.environ.get("MATTERBOT_JIRA_PASSWORD")
))

STATUSES_EMOJI = {
    "A faire": ":new:",
    "En cours": ":hammer_and_wrench:",
    "Needs Review": ":clock1:",
    "Fini": ":white_check_mark:",
    "Canceled": ":x:",
}


@respond_to('{} issues'.format(PROJECT), re.IGNORECASE)
def issues(message):
    """Print opened issues"""
    issues = JIRA_CONNECTOR.search_issues(
        """project={} and
        status != Done and
        status != Canceled and
        (type = Bogue or type = Story)
        """.format(PROJECT)
    )

    lines = []
    for issue in issues:
        lines.append([
            "[{0}]({1}/browse/{0})".format(issue.key, JIRA_URL),
            issue.fields.summary,
            STATUSES_EMOJI[issue.fields.status.name],
        ])
    message.send(build_array(["IKA", "Summary", "Status"], lines))


@respond_to('{} sprint'.format(PROJECT), re.IGNORECASE)
def active_sprint(message):
    """Print active sprint issues"""
    issues = JIRA_CONNECTOR.search_issues(
        """project={} and
        status != Done and
        status != Canceled and
        (type = Bogue or type = Story)
        and sprint in openSprints()
        order by status desc
        """.format(PROJECT)
    )

    lines = []
    for issue in issues:
        lines.append([
            "[{0}]({1}/browse/{0})".format(issue.key, JIRA_URL),
            issue.fields.summary,
            STATUSES_EMOJI[issue.fields.status.name],
        ])
    message.send(build_array(["IKA", "Summary", "Status"], lines))


@respond_to('{} issue (.*)'.format(PROJECT), re.IGNORECASE)
def get_issue(message, key=None):
    """Get issue detail from its key"""
    issue = JIRA_CONNECTOR.issue(key)
    lines = []
    lines.append("[{0}]({1}/browse/{0})".format(issue.key, JIRA_URL))
    lines.append(issue.fields.summary)
    lines.append("{} - {}".format(
        STATUSES_EMOJI[issue.fields.status.name],
        issue.fields.status.name
    ))
    if issue.fields.assignee:
        lines.append(issue.fields.assignee.displayName)
    else:
        line.append("Not assigned")
    message.send(build_array(["IKA issue"], lines))


@respond_to('{} assign (.*)'.format(PROJECT), re.IGNORECASE)
@respond_to('{} assign (.*) to (.*)'.format(PROJECT), re.IGNORECASE)
def assign_issue(message, key=None, user=None):
    """Assign issue to user by default me"""
    if key:
        issue = JIRA_CONNECTOR.issue(key)
        if not user:
            # get current user by his mail
            mail = message.get_user_mail()
            users = JIRA_CONNECTOR.search_assignable_users_for_projects(
                "", PROJECT)
            match = [u for u in users if u.emailAddress == mail]
            if match:
                user = match[0].name
            else:
                message.send('Can not retrieve user from mail')

        if user:
            JIRA_CONNECTOR.assign_issue(issue, user)
    else:
        message.send('You need to specify a key')


def build_array(headers, contents):
    """Build array in mattermost format from headers and contents"""
    def build_line(line_content):
        if not isinstance(line_content, list):
            line_content = [line_content]

        line_content.insert(0, "")
        line_content.append("")
        return " | ".join(line_content)

    lines = [
        build_line(["**{}**".format(header) for header in headers]),
        build_line([":-"] * len(headers))
    ]
    lines.extend([build_line(content) for content in contents])
    return "\n".join(lines)
