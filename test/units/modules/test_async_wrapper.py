# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations


import os
import json
import shutil
import sys
import tempfile

from ansible.modules import async_wrapper


class TestAsyncWrapper:

    def test_run_module(self, monkeypatch):

        module_result = {'rc': 0}
        module_lines = [
            'import sys',
            'sys.stderr.write("stderr stuff")',
            "print('%s')" % json.dumps(module_result)
        ]
        module_data = '\n'.join(module_lines) + '\n'
        module_data = module_data.encode('utf-8')

        workdir = tempfile.mkdtemp()
        fh, fn = tempfile.mkstemp(dir=workdir)

        with open(fn, 'wb') as f:
            f.write(module_data)

        command = fn
        jobid = 0
        job_path = os.path.join(os.path.dirname(command), 'job')

        monkeypatch.setattr(async_wrapper, 'job_path', job_path)

        res = async_wrapper._run_module(jobid, sys.executable, command)

        with open(os.path.join(workdir, 'job'), 'r') as f:
            jres = json.loads(f.read())

        shutil.rmtree(workdir)

        assert jres.get('rc') == 0
        assert jres.get('stderr') == 'stderr stuff'

    def test_run_module_ipc_send_failure(self, monkeypatch):
        # Regression test for https://github.com/ansible/ansible/issues/87387:
        # when the parent wrapper process exits before the worker signals task
        # start over the IPC pipe, the send raises BrokenPipeError. The worker
        # must record a failure result instead of crashing and leaving the job
        # file at finished: False, which would make async_status poll until the
        # async timeout.
        module_result = {'rc': 0}
        module_lines = [
            'import sys',
            "print('%s')" % json.dumps(module_result)
        ]
        module_data = '\n'.join(module_lines) + '\n'
        module_data = module_data.encode('utf-8')

        workdir = tempfile.mkdtemp()
        fh, fn = tempfile.mkstemp(dir=workdir)
        with open(fn, 'wb') as f:
            f.write(module_data)

        job_path = os.path.join(os.path.dirname(fn), 'job')
        monkeypatch.setattr(async_wrapper, 'job_path', job_path)

        class BrokenNotifier:
            def send(self, value):
                raise BrokenPipeError(32, 'Broken pipe')

            def close(self):
                pass

        monkeypatch.setattr(async_wrapper, 'ipc_notifier', BrokenNotifier())

        res = async_wrapper._run_module(0, sys.executable, fn)

        with open(job_path, 'r') as f:
            jres = json.loads(f.read())

        shutil.rmtree(workdir)

        assert jres.get('started') is True
        assert jres.get('finished') is True
        assert jres.get('failed') is True
        assert jres.get('ansible_job_id') == 0

    def test_record_failure_if_incomplete_stale_marker(self, monkeypatch):
        # A worker that died mid-run leaves the job file at started/finished
        # markers; the watcher must overwrite with a failure result so the
        # poller stops instead of waiting for the async timeout.
        workdir = tempfile.mkdtemp()
        job_path = os.path.join(workdir, 'job')
        monkeypatch.setattr(async_wrapper, 'job_path', job_path)

        with open(job_path, 'w') as f:
            json.dump({"started": True, "finished": False, "ansible_job_id": "x.1"}, f)

        async_wrapper._record_failure_if_incomplete("x.1", 4242)

        with open(job_path, 'r') as f:
            jres = json.loads(f.read())

        shutil.rmtree(workdir)

        assert jres.get('started') is True
        assert jres.get('finished') is True
        assert jres.get('failed') is True
        assert jres.get('child_pid') == 4242

    def test_record_failure_if_incomplete_final_result(self, monkeypatch):
        # A worker that wrote a final result must not be overwritten by the
        # watcher's failure path.
        workdir = tempfile.mkdtemp()
        job_path = os.path.join(workdir, 'job')
        monkeypatch.setattr(async_wrapper, 'job_path', job_path)

        final_result = {"rc": 0, "changed": True, "started": True, "finished": True}
        with open(job_path, 'w') as f:
            json.dump(final_result, f)

        async_wrapper._record_failure_if_incomplete("x.2", 4243)

        with open(job_path, 'r') as f:
            jres = json.loads(f.read())

        shutil.rmtree(workdir)

        assert jres.get('rc') == 0
        assert jres.get('changed') is True
        assert jres.get('failed') is not True

    def test_record_failure_if_incomplete_missing_job_file(self, monkeypatch):
        # A worker that died before writing anything leaves no job file; the
        # watcher must create one with a failure result.
        workdir = tempfile.mkdtemp()
        job_path = os.path.join(workdir, 'job')
        monkeypatch.setattr(async_wrapper, 'job_path', job_path)

        async_wrapper._record_failure_if_incomplete("x.3", 4244)

        assert os.path.exists(job_path)
        with open(job_path, 'r') as f:
            jres = json.loads(f.read())

        shutil.rmtree(workdir)

        assert jres.get('failed') is True
        assert jres.get('finished') is True
