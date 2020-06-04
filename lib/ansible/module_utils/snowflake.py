#!/usr/bin/python

# -*- coding: utf-8 -*-

# Copyright: (c) 2020, Nate Fleming <nate.fleming@moserit.com>
# Sponsored by Moser Consulting Inc http://www.moserit.com
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import os
import traceback

from ansible.module_utils.basic import missing_required_lib
from ansible.module_utils._text import to_native


snowflake_missing_lib_exception = None
snowflake_missing_lib_msg = missing_required_lib('snowflake')
snowflake_found = True

try:
    import snowflake.connector
except ImportError:
    snowflake_missing_lib_exception = traceback.format_exc()
    snowflake_found = False


DEFAULT_ACCOUNT = os.getenv('SNOWSQL_ACCOUNT')
DEFAULT_USER = os.getenv('SNOWSQL_USER')
DEFAULT_PWD = os.getenv('SNOWSQL_PWD')
DEFAULT_WAREHOUSE = os.getenv('SNOWSQL_WAREHOUSE')
DEFAULT_DATABASE = os.getenv('SNOWSQL_DATABASE')
DEFAULT_SCHEMA = os.getenv('SNOWSQL_SCHEMA', 'PUBLIC')
DEFAULT_ROLE = os.getenv('SNOWSQL_ROLE')


def snowflake_connect(params):

    DEFAULT_CONNECTION = {
        "account": DEFAULT_ACCOUNT,
        "user": DEFAULT_USER,
        "password": DEFAULT_PWD,
        "role": DEFAULT_ROLE,
        "warehouse": DEFAULT_WAREHOUSE,
        "schema": DEFAULT_SCHEMA
    }

    options = DEFAULT_CONNECTION

    options.update(params)
    options = {key: value for (key, value) in options.items() if value}

    connection = snowflake.connector.connect(**options)

    return connection


def quoted_identifier(target):
    return "'{0}'".format(target)


def fully_qualify(*args):
    return '.'.join([x.strip() for x in args if x.strip()])



