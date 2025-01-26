#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import unittest
from unittest.mock import patch, MagicMock

from ansible.executor.process.worker import WorkerProcess

class TestWorkerProcess(unittest.TestCase):
    def test_fault_handler_setup(self):
        """Test that fault handler is properly set up in worker process"""
        with patch('ansible.executor.process.worker.setup_fault_handler') as mock_setup:
            worker = WorkerProcess(
                final_q=MagicMock(),
                task_vars={},
                host=MagicMock(),
                task=MagicMock(),
                play_context=MagicMock(),
                loader=MagicMock(),
                variable_manager=MagicMock(),
                shared_loader_obj=MagicMock(),
                worker_id='test_worker'
            )
            mock_setup.assert_called_once_with('test_worker')
