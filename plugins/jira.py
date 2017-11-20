#!/usr/bin/python3
# -*- coding: utf-8 -*-

import re
import os

from jira import JIRA
from mattermost_bot.bot import respond_to

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


@respond_to("{} issues".format(PROJECT), re.IGNORECASE)
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


@respond_to("{} sprint".format(PROJECT), re.IGNORECASE)
def active_sprint(message):
    """Print sprint issues"""
    issues = JIRA_CONNECTOR.search_issues(
        """project={} and
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


@respond_to("{} issue (\w*)".format(PROJECT), re.IGNORECASE)
def get_issue(message, key=None):
    """Get issue detail from its key"""
    issue = get_jira_issue_from_key(key, message)
    if issue:
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
            lines.append("Not assigned")
        message.send(build_array(["IKA issue"], lines))


@respond_to("{} assign (\w*)".format(PROJECT), re.IGNORECASE)
@respond_to("{} assign (\w*) to (@*\w*)".format(PROJECT), re.IGNORECASE)
def assign_issue(message, key=None, username=None):
    """Assign issue to user by default me"""
    issue = get_jira_issue_from_key(key, message)
    if issue:

        if not username:
            # get current user by his mail
            mail = message.get_user_mail()
        else:
            users = message._client.get_users().values()
            user = [
                u for u in users if u["username"] == username.replace("@", "")
            ]
            if user:
                mail = user[0]["email"]
            else:
                message.send("Can not find jira user from {}".format(username))

        if mail:
            jira_users = JIRA_CONNECTOR.search_assignable_users_for_projects(
                "", PROJECT)
            match = [u for u in jira_users if u.emailAddress == mail]
            if match:
                user = match[0].name
                JIRA_CONNECTOR.assign_issue(issue, user)
                message.send("Issue {} assigned to {}".format(key, user))
            else:
                message.send("Can not retrieve user from mail {}".format(mail))


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


def get_jira_issue_from_key(issue_key, message):
    """Try to get jira issue from key or send an error message"""
    if not issue_key.upper().startswith(PROJECT.upper()):
        issue_key = "{}-{}".format(PROJECT, issue_key)

    try:
        return JIRA_CONNECTOR.issue(issue_key)
    except:
        message.send("Invalid issue key : {}".format(issue_key))
        return None
