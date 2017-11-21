#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

BOT_URL = os.environ.get("MATTERBOT_URL")
BOT_LOGIN = os.environ.get("MATTERBOT_LOGIN")
BOT_PASSWORD = os.environ.get("MATTERBOT_PASSWORD")
BOT_TEAM = os.environ.get("MATTERBOT_TEAM")
IGNORE_NOTIFIES = os.environ.get("MATTERBOT_IGNORE")

PLUGINS = [
    "mattermost_bot.plugins",
    "plugins",
]
