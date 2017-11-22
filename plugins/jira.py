#!/usr/bin/python3
# -*- coding: utf-8 -*-

import re
import os

from plugins import MATTERMOST_MESSAGE_MAX_LENGTH
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
        line = [
            "[{0}]({1}/browse/{0})".format(issue.key, JIRA_URL),
            issue.fields.summary,
            STATUSES_EMOJI[issue.fields.status.name],
        ]
        if issue.fields.assignee:
            line.append(issue.fields.assignee.displayName)
        else:
            line.append("Not assigned")
        lines.append(line)

    build_tables(message, ["IKA", "Summary", "Status", "Assignee"], lines)


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
        line = [
            "[{0}]({1}/browse/{0})".format(issue.key, JIRA_URL),
            issue.fields.summary,
            STATUSES_EMOJI[issue.fields.status.name],
        ]
        if issue.fields.assignee:
            line.append(issue.fields.assignee.displayName)
        else:
            line.append("Not assigned")
        lines.append(line)

    build_tables(message, ["IKA", "Summary", "Status", "Assignee"], lines)


@respond_to("{} issue (\w*)".format(PROJECT), re.IGNORECASE)
def get_issue(message, key=None):
    """Get issue detail from its key"""
    issue = get_jira_issue_from_key(key, message)
    if issue:

        lines = [
            "[{0}]({1}/browse/{0})".format(issue.key, JIRA_URL),
            issue.fields.summary,
            "{} - {}".format(
                STATUSES_EMOJI[issue.fields.status.name],
                issue.fields.status.name)
        ]
        if issue.fields.assignee:
            lines.append("Assigned to : {}".format(
                issue.fields.assignee.displayName,
            ))
        else:
            lines.append("Not assigned")
        lines.append("Created by : {} on {}".format(
            issue.fields.creator.displayName,
            issue.fields.created,
            ))
        build_tables(message, ["IKA issue"], lines)


@respond_to("{} assign (\w*$)".format(PROJECT), re.IGNORECASE)
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
                message.send(
                    "**Error** : Can not retrieve user from mail {}".format(
                        mail)
                )


@respond_to("{} begin (\w*)".format(PROJECT), re.IGNORECASE)
def begin(message, key=None):
    """Set issue status to `in progress`"""
    make_transitions(message, key, "Begin")


@respond_to("{} code (\w*)".format(PROJECT), re.IGNORECASE)
def code(message, key=None):
    """Set issue status to `needs review`"""
    make_transitions(message, key, "Code")


@respond_to("{} review (\w*)".format(PROJECT), re.IGNORECASE)
def review(message, key=None):
    """Set issue status to `done`"""
    make_transitions(message, key, "Review")


@respond_to("{} cancel (\w*)".format(PROJECT), re.IGNORECASE)
def cancel(message, key=None):
    """Set issue status to `canceled`"""
    make_transitions(message, key, "Cancel")


def make_transitions(message, key=None, transition=None):
    """Make transitions for jira issues
    Valid transitions are ("begin", "code", "review", "cancel")
    """
    issue = get_jira_issue_from_key(key, message)
    if issue:
        transitions = {
            t["name"]: t["id"] for t in JIRA_CONNECTOR.transitions(issue)
        }
        if transition in transitions:
            JIRA_CONNECTOR.transition_issue(issue, transitions[transition])
            message.send("{} {} {}".format(
                message.get_username(), transition, key
            ))
        else:
            message.send(
                "**ERROR** : '{}' is not a valid transition for {}".format(
                    transition, key)
            )


def build_tables(message, headers, contents):
    """Build table(s) in mattermost format from headers and contents,
    if the message length is superior to MATTERMOST_MESSAGE_MAX_LENGTH
    into several messages
    """
    def build_line(line_content):
        if not isinstance(line_content, list):
            line_content = [line_content]

        line_content.insert(0, "")
        line_content.append("")
        return " | ".join(line_content)

    header = [
        build_line(["**{}**".format(header) for header in headers]),
        build_line([":-"] * len(headers)),
        ""
    ]

    tables = []
    markdown = "\n".join(header)

    for content in contents:
        new_line = build_line(content)
        if len(new_line) + len(markdown) >= MATTERMOST_MESSAGE_MAX_LENGTH:
            tables.append(markdown)
            markdown = "\n".join(header)

        markdown += new_line + "\n"

    if markdown:
        tables.append(markdown)

    for table in tables:
        message.send(table)


def get_jira_issue_from_key(issue_key, message):
    """Try to get jira issue from key or send an error message"""
    if not issue_key.upper().startswith(PROJECT.upper()):
        issue_key = "{}-{}".format(PROJECT, issue_key)

    try:
        return JIRA_CONNECTOR.issue(issue_key)
    except:
        message.send("**ERROR** : Invalid issue key : {}".format(issue_key))
        return None
