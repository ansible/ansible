#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: lework
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: wechat
version_added: "2.9"
short_description: Send a message to Wechat.
description:
   - Send a message to Wechat.
options:
  corpid:
    description:
      - Business id.
    required: true
    type: str
  secret:
    description:
      - application secret.
    required: true
    type: str
  agentid:
    description:
      - application id.
    required: true
    type: str
  touser:
    description:
      - Member ID list (message recipient, multiple recipients separated by '|', up to 1000).
      - "Special case: Specify @all to send to all members of the enterprise application."
      -  When toparty, touser, totag is empty, the default value is @all.
    type: str
  toparty:
    description:
      - A list of department IDs. Multiple recipients are separated by '|' and support up to 100. Ignore this parameter when touser is @all
    type: str
  totag:
    description:
      - A list of tag IDs, separated by '|' and supported by up to 100. Ignore this parameter when touser is @all
    type: str
  msg:
    description:
      - The message body.
    required: true
    type: str
author:
- lework (@lework)
'''

EXAMPLES = '''
# Send all users.
- wechat:
    corpid: "123"
    secret: "456"
    agentid: "100001"
    msg: Ansible task finished

# Send a user.
- wechat:
    corpid: "123"
    secret: "456"
    agentid: "100001"
    touser: "LeWork"
    msg: Ansible task finished

# Send multiple user.
- wechat:
    corpid: "123"
    secret: "456"
    agentid: "100001"
    touser: "LeWork|Lework1|Lework2"
    msg: Ansible task finished

# Send a department.
- wechat:
    corpid: "123"
    secret: "456"
    agentid: "100001"
    toparty: "10"
    msg: Ansible task finished
'''

RETURN = """
msg:
  description: The message you attempted to send
  returned: success,failure
  type: str
  sample: "Ansible task finished"
touser:
  description: send user id
  returned: success
  type: str
  sample: "ZhangSan"
toparty:
  description: send department id
  returned: success
  type: str
  sample: "10"
totag:
  description: send tag id
  returned: success
  type: str
  sample: "dev"
wechat_error:
  description: Error message gotten from Wechat API
  returned: failure
  type: str
  sample: "Bad Request: message text is empty"
"""


# ===========================================
# WeChat module specific support methods.
#

import json
import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
from ansible.module_utils.urls import fetch_url


class WeChat(object):
    def __init__(self, module, corpid, secret, agentid):
        self.module = module
        self.url = 'https://qyapi.weixin.qq.com'
        self.corpid = corpid
        self.secret = secret
        self.agentid = agentid
        self.token = ''
        self.msg = ''

        if self.module.check_mode:
            module.exit_json(changed=False)

        self.access_token()

    def access_token(self):
        """
        get access_token
        :return:
        """
        url_arg = '/cgi-bin/gettoken?corpid={id}&corpsecret={crt}'.format(
            id=self.corpid, crt=self.secret)
        url = self.url + url_arg
        response, info = fetch_url(self.module, url=url)
        text = response.read()
        try:
            self.token = json.loads(text)['access_token']
        except Exception as e:
            raise Exception("Invalid corpid or corpsecret, api result:%s" % text)

    def messages(self, msg, touser, toparty, totag):
        """
        Message body
        :param msg: message info
        :param touser: user id
        :param toparty: department id
        :param totag: tag id
        :return:
        """
        values = {
            "msgtype": 'text',
            "agentid": self.agentid,
            "text": {'content': msg},
            "safe": 0
        }

        if touser:
            values['touser'] = touser
        if toparty:
            values['toparty'] = toparty
        if toparty:
            values['totag'] = totag

        self.msg = json.dumps(values)

    def send_message(self, msg, touser=None, toparty=None, totag=None):
        """
        send message
        :param msg: message info
        :param touser:  user id
        :param toparty:  department id
        :param totag: tag id
        :return:
        """
        self.messages(msg, touser, toparty, totag)

        send_url = '{url}/cgi-bin/message/send?access_token={token}'.format(
            url=self.url, token=self.token)
        response, info = fetch_url(self.module, url=send_url, data=self.msg, method='POST')
        text = json.loads(response.read())
        if text['invaliduser'] != '':
            raise Exception("invalid user: %s" % text['invaliduser'])


def main():
    module = AnsibleModule(
        argument_spec=dict(
            corpid=dict(required=True, no_log=True),
            secret=dict(required=True, no_log=True),
            agentid=dict(required=True,),
            msg=dict(required=True,),
            touser=dict(),
            toparty=dict(),
            totag=dict(),
        ),
        supports_check_mode=True
    )

    corpid = module.params["corpid"]
    secret = module.params["secret"]
    agentid = module.params["agentid"]
    msg = module.params["msg"]
    touser = module.params["touser"]
    toparty = module.params["toparty"]
    totag = module.params["totag"]

    try:
        if not touser and not toparty and not totag:
            touser = "@all"

        wechat = WeChat(module, corpid, secret, agentid)
        wechat.send_message(msg, touser, toparty, totag)

    except Exception as e:
        module.fail_json(msg="unable to send msg: %s" % msg, wechat_error=to_native(e), exception=traceback.format_exc())

    changed = True
    module.exit_json(changed=changed, touser=touser, toparty=toparty, totag=totag, msg=msg)


if __name__ == '__main__':
    main()
