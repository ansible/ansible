from __future__ import (absolute_import, division, print_function)

import time
import uuid

__metaclass__ = type

DOCUMENTATION = '''
    callback: cloudwatch_logs
    callback_type: notification
    requirements:
      - whitelist in configuration
      - boto3 (python library)
    short_description: Sends play events AWS CloudWatch Logs
    version_added: "2.5.4"
    description:
        - This is an ansible callback plugin that sends status updates to CloudWatch Logs during playbook execution.
    options:
      log_group_name:
        required: True
        description: group name the logs are written against
        env:
          - name: CLOUDWATCH_LOGS_LOG_GROUP_NAME
        ini:
          - section: callback_cloudwatch_logs
            key: log_group_name
            
      log_stream_name:
        required: True
        description: stream name the logs are written against
        env:
          - name: CLOUDWATCH_LOGS_LOG_STREAM_NAME
        ini:
          - section: callback_cloudwatch_logs
            key: log_stream_name
            
      aws_region_name:
        required: False
        description: aws region to use
        env:
          - name: CLOUDWATCH_LOGS_AWS_REGION_NAME
        ini:
          - section: callback_cloudwatch_logs
            key: aws_region_name
            
      aws_access_key_id:
        required: False
        description: aws credentials
        env:
          - name: CLOUDWATCH_LOGS_AWS_ACCESS_KEY_ID
        ini:
          - section: callback_cloudwatch_logs
            key: aws_access_key_id
            
      aws_secret_access_key:
        required: False
        description: aws credentials
        env:
          - name: CLOUDWATCH_LOGS_AWS_SECRET_ACCESS_KEY
        ini:
          - section: callback_cloudwatch_logs
            key: aws_secret_access_key
            
      aws_kms_key_id:
        required: False
        description: id of the kms key to encrypt the logs with
        env:
          - name: CLOUDWATCH_LOGS_AWS_KMS_KEY_ID
        ini:
          - section: callback_cloudwatch_logs
            key: aws_kms_key_id
'''

import getpass
import os
import boto3
from ansible.plugins.callback import CallbackBase
from ansible.playbook.task_include import TaskInclude


class CallbackModule(CallbackBase):
    CALLBACK_VERSION = 2.0
    CALLBACK_NAME = 'cloudwatch_logs'
    CALLBACK_TYPE = 'notification'
    CALLBACK_NEEDS_WHITELIST = True

    def __init__(self, display=None):
        super(CallbackModule, self).__init__(display=display)
        self.boto_client = None
        self.logger = None

        self.log_group_name = None
        self.log_stream_name = None
        self.aws_access_key_id = None
        self.aws_region_name = None
        self.aws_secret_access_key = None
        self.aws_kms_key_id = None

        self.username = getpass.getuser()
        self.playbook_name = None
        self._pending_logs = []
        self.next_sequence_token = None
        self.playbook_id = uuid.uuid4()

    def set_options(self, task_keys=None, var_options=None, direct=None):
        super(CallbackModule, self).set_options(task_keys=task_keys,
                                                var_options=var_options,
                                                direct=direct)

        self.log_group_name = self.get_option('log_group_name')
        self.log_stream_name = self.get_option('log_stream_name')
        self.aws_region_name = self.get_option('aws_region_name')
        self.aws_access_key_id = self.get_option('aws_access_key_id')
        self.aws_secret_access_key = self.get_option('aws_secret_access_key')
        self.aws_kms_key_id = self.get_option('aws_kms_key_id')

        if self.aws_secret_access_key and self.aws_access_key_id:
            self.boto_client = boto3.client('logs',
                                            region_name=self.aws_region_name,
                                            aws_access_key_id=self.aws_access_key_id,
                                            aws_secret_access_key=self.aws_secret_access_key)
        else:
            self.boto_client = boto3.client('logs',
                                            region_name=self.aws_region_name)

        if not LogGroupPaginator(self.boto_client, self.log_group_name
                                      ).exists(self.log_group_name):
            self.create_log_group(self.boto_client, self.log_group_name)

        log_stream_paginator = LogStreamPaginator(self.boto_client,self.log_group_name, self.log_stream_name)
        if not log_stream_paginator.exists(self.log_stream_name):
            self.create_log_stream(self.boto_client, self.log_group_name, self.log_stream_name)

        self.next_sequence_token = log_stream_paginator.sequence_token

    def create_log_group(self, client, log_group_name):
        if self.aws_kms_key_id:
            client.create_log_group(
                logGroupName=log_group_name,
                kmsKeyId=self.aws_kms_key_id,
            )
        else:
            client.create_log_group(
                logGroupName=log_group_name,
            )

    def create_log_stream(self, client, log_group_name, log_stream_name):
        client.create_log_stream(
            logGroupName=log_group_name,
            logStreamName=log_stream_name
        )

    def _send_log_to_cloudwatch(self):
        if self.next_sequence_token:
            response = self.boto_client.put_log_events(
                logGroupName=self.log_group_name,
                logStreamName=self.log_stream_name,
                logEvents=self._pending_logs,
                sequenceToken=self.next_sequence_token
            )
        else:
            response = self.boto_client.put_log_events(
                logGroupName=self.log_group_name,
                logStreamName=self.log_stream_name,
                logEvents=self._pending_logs,
            )
        self.next_sequence_token = response['nextSequenceToken']

    def _send_log(self, status, message):
        self._pending_logs.append(
            dict(
                timestamp=int(time.time() * 1000),
                message='{} - PlaybookId[{}] {}: {}'.format(self.username, self.playbook_id, status, message)
            )
        )

    def v2_runner_on_failed(self, result, ignore_errors=False):
        if ignore_errors:
            return
        host = result._host
        self._send_log('failed: ', '[{}]'.format(host.get_name()))

    def v2_runner_on_ok(self, _result):
        host = _result._host
        task = _result._task
        result = _result._result

        if isinstance(task, TaskInclude):
            return
        elif result.get('changed', False):
            msg = [['changed: ']]
        else:
            msg = [['ok: ']]

        delegated_vars = result.get('_ansible_delegated_vars', None)
        if delegated_vars:
            msg.append("[{} -> {}]".format(host.get_name(), delegated_vars['ansible_host']))
        else:
            msg.append("[{}]".format(host.get_name()))

        if task.loop and 'results' in result:
            self._process_items(_result)
        else:
            self._clean_results(result, task.action)

            if (self._display.verbosity > 0 or '_ansible_verbose_always' in result) \
                    and '_ansible_verbose_override' not in result:
                msg[1] += " => {}".format(result)
        self._send_log(*msg)

    def v2_runner_on_skipped(self, result):
        host = result._host
        self._send_log('skipped: ', '[{}]'.format(host.get_name()))

    def v2_runner_on_unreachable(self, result):
        host = result._host
        self._send_log('unreachable: ', '[{}]'.format(host.get_name))

    def v2_playbook_on_start(self, playbook):
        self.playbook_name = os.path.basename(playbook._file_name)
        self._send_log('playbook started', self.playbook_name)

    def v2_playbook_on_task_start(self, task, is_conditional):
        self._send_log('task started', task)

    def v2_playbook_on_play_start(self, play):
        name = play.name or 'Play name not specified'
        self._send_log('play started', name)

    def v2_runner_item_on_failed(self, result):
        host = result._host
        self._send_log('item failed', '[{}]'.format(host.get_name()))

    def v2_runner_item_on_skipped(self,result):
        host = result._host
        self._send_log('item skipped', '[{}]'.format(host.get_name()))

    def v2_runner_retry(self, result):
        host = result._host
        self._send_log('retry', '[{}]'.format(host.get_name()))

    def v2_playbook_on_stats(self, stats):
        """Display info about playbook statistics"""
        hosts = sorted(stats.processed.keys())
        ok = 0
        changed = 0
        failures = 0
        unreachable = 0
        for h in hosts:
            s = stats.summarize(h)
            ok += s['ok']
            changed += s['changed']
            failures += s['failures']
            unreachable += s['unreachable']

        status_line = 'OK:{} CHANGED:{} FAILURES:{} UNREACHABLE:{}'.format(
            ok, changed, failures, unreachable
        )

        if failures or unreachable:
            final_status = 'Failed'
        else:
            final_status = 'Succeeded'

        self._send_log('COMPLETE', 'Playbook {}. {}'.format(final_status, status_line))
        self._send_log_to_cloudwatch()


class LogStreamPaginator(object):
    def __init__(self, client, log_group_name, prefix):
        self.log_group_name = log_group_name
        self.client = client
        self.prefix = prefix
        self.next_token = None
        self.order_by = 'LogStreamName'
        self.descending = True
        self.sequence_token = None

    def __iter__(self):
        return self

    def __next__(self):
        if self.next_token:
            response = self.client.describe_log_streams(
                logGroupName=self.log_group_name,
                logStreamNamePrefix=self.prefix,
                orderBy=self.order_by,
                descending=self.descending,
                nextToken=self.next_token,
            )
        else:
            response = self.client.describe_log_streams(
                logGroupName=self.log_group_name,
                logStreamNamePrefix=self.prefix,
                orderBy=self.order_by,
                descending=self.descending,
            )

        if response and len(response['logStreams']) > 0:
            self._last_response = response
            self.next_token = response.get('nextToken')
            return [[s['logStreamName'], s['uploadSequenceToken']] for s in response['logStreams']]
        else:
            self.next_token = None
            raise StopIteration

    def exists(self, stream_name):
        for streams in self:
            for name, token in streams:
                if name == stream_name:
                    self.sequence_token = token or None
                    return True
        return False

    # python2 compatibility
    next = __next__


class LogGroupPaginator(object):
    def __init__(self, client, prefix):
        self.client = client
        self.prefix = prefix
        self.next_token = None

    def __iter__(self):
        return self

    def __next__(self):
        if self.next_token:
            response = self.client.describe_log_groups(
                logGroupNamePrefix=self.prefix,
                nextToken=self.next_token,
            )
        else:
            response = self.client.describe_log_groups(
                logGroupNamePrefix=self.prefix,
            )

        if response and len(response['logGroups']) > 0:
            self.next_token = response.get('nextToken')
            return [l['logGroupName'] for l in response['logGroups']]
        else:
            self.next_token = None
            raise StopIteration

    def exists(self, group_name):
        for groups in self:
            if group_name in groups:
                return True
        return False

    next = __next__
