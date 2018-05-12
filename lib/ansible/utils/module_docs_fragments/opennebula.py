# -*- coding: utf-8 -*-
#
# Copyright 2018 www.privaz.io Valletech AB
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment(object):
    # OpenNebula common documentation
    DOCUMENTATION = '''
options:
    endpoint:
        description:
            - The URL of the XMLRPC server.
              If not specified then the value of the PYONE_ENDPOINT environment variable, if any, is used.
    session:
        description:
            - Session string associated to the connected user.
              It has to be formed with the contents of OpenNebula's ONE_AUTH file, which is <username>:<password>
              with the default "core" auth driver.
              If not specified then the value of the PYONE_SESSION environment variable, if any, is used.
    validate_certs:
        description:
            - Whether to validate the SSL certificates or not.
              This parameter is ignored if PYTHONHTTPSVERIFY environment variable is used.
        default: true
    wait_timeout:
        description:
            - time to wait for the desired state to be reached before timeout, in seconds.
        default: 300
'''
