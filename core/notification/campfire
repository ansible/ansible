#!/usr/bin/python
# -*- coding: utf-8 -*-

DOCUMENTATION = '''
---
module: campfire
version_added: "1.2"
short_description: Send a message to Campfire
description:
   - Send a message to Campfire.
   - Messages with newlines will result in a "Paste" message being sent.
version_added: "1.2"
options:
  subscription:
    description:
      - The subscription name to use.
    required: true
  token:
    description:
      - API token.
    required: true
  room:
    description:
      - Room number to which the message should be sent.
    required: true
  msg:
    description:
      - The message body.
    required: true
  notify:
    description:
      - Send a notification sound before the message.
    required: false
    choices: ["56k", "bell", "bezos", "bueller", "clowntown",
              "cottoneyejoe", "crickets", "dadgummit", "dangerzone",
              "danielsan", "deeper", "drama", "greatjob", "greyjoy",
              "guarantee", "heygirl", "horn", "horror",
              "inconceivable", "live", "loggins", "makeitso", "noooo",
              "nyan", "ohmy", "ohyeah", "pushit", "rimshot",
              "rollout", "rumble", "sax", "secret", "sexyback",
              "story", "tada", "tmyk", "trololo", "trombone", "unix",
              "vuvuzela", "what", "whoomp", "yeah", "yodel"]

# informational: requirements for nodes
requirements: [ urllib2, cgi ]
author: Adam Garside <adam.garside@gmail.com>
'''

EXAMPLES = '''
- campfire: subscription=foo token=12345 room=123 msg="Task completed."

- campfire: subscription=foo token=12345 room=123 notify=loggins
        msg="Task completed ... with feeling."
'''


def main():

    try:
        import urllib2
    except ImportError:
        module.fail_json(msg="urllib2 is required")

    try:
        import cgi
    except ImportError:
        module.fail_json(msg="cgi is required")

    module = AnsibleModule(
        argument_spec=dict(
            subscription=dict(required=True),
            token=dict(required=True),
            room=dict(required=True),
            msg=dict(required=True),
            notify=dict(required=False,
                        choices=["56k", "bell", "bezos", "bueller",
                                 "clowntown", "cottoneyejoe",
                                 "crickets", "dadgummit", "dangerzone",
                                 "danielsan", "deeper", "drama",
                                 "greatjob", "greyjoy", "guarantee",
                                 "heygirl", "horn", "horror",
                                 "inconceivable", "live", "loggins",
                                 "makeitso", "noooo", "nyan", "ohmy",
                                 "ohyeah", "pushit", "rimshot",
                                 "rollout", "rumble", "sax", "secret",
                                 "sexyback", "story", "tada", "tmyk",
                                 "trololo", "trombone", "unix",
                                 "vuvuzela", "what", "whoomp", "yeah",
                                 "yodel"]),
        ),
        supports_check_mode=False
    )

    subscription = module.params["subscription"]
    token = module.params["token"]
    room = module.params["room"]
    msg = module.params["msg"]
    notify = module.params["notify"]

    URI = "https://%s.campfirenow.com" % subscription
    NSTR = "<message><type>SoundMessage</type><body>%s</body></message>"
    MSTR = "<message><body>%s</body></message>"
    AGENT = "Ansible/1.2"

    try:

        # Setup basic auth using token as the username
        pm = urllib2.HTTPPasswordMgrWithDefaultRealm()
        pm.add_password(None, URI, token, 'X')

        # Setup Handler and define the opener for the request
        handler = urllib2.HTTPBasicAuthHandler(pm)
        opener = urllib2.build_opener(handler)

        target_url = '%s/room/%s/speak.xml' % (URI, room)

        # Send some audible notification if requested
        if notify:
            req = urllib2.Request(target_url, NSTR % cgi.escape(notify))
            req.add_header('Content-Type', 'application/xml')
            req.add_header('User-agent', AGENT)
            response = opener.open(req)

        # Send the message
        req = urllib2.Request(target_url, MSTR % cgi.escape(msg))
        req.add_header('Content-Type', 'application/xml')
        req.add_header('User-agent', AGENT)
        response = opener.open(req)

    except urllib2.HTTPError, e:
        if not (200 <= e.code < 300):
            module.fail_json(msg="unable to send msg: '%s', campfire api"
                                 " returned error code: '%s'" %
                                 (msg, e.code))

    except Exception, e:
        module.fail_json(msg="unable to send msg: %s" % msg)

    module.exit_json(changed=True, room=room, msg=msg, notify=notify)

# import module snippets
from ansible.module_utils.basic import *
main()
