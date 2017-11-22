#!/usr/bin/env python
# -*- coding: utf-8 -*-

from functools import wraps


MATTERMOST_MESSAGE_MAX_LENGTH = 4000


def only_from_users(usernames):
    """Restrict enpoint only for given user names"""
    def wrapper(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            message = args[0]
            username = message.get_username()
            if username not in usernames:
                message.send(
                    "**Error** : You don't have access to this functionnality"
                )
            else:
                return func(*args, **kwargs)
        return wrapped
    return wrapper
