# (c) 2026 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import os
import shutil
import tempfile
import unittest

from ansible.executor.rollback_manager import (
    AnsibleRollbackError,
    JournalEntry,
    RollbackManager,
    RollbackPolicy,
    TransactionJournal,
    TransactionStatus,
    UndoAction,
    UnsupportedAtomicModuleError,
)


class TestRollbackManager(unittest.TestCase):

    def setUp(self):
        self.temp_storage = tempfile.mkdtemp(prefix="ansible_test_journal_")

    def tearDown(self):
        shutil.rmtree(self.temp_storage, ignore_errors=True)

    def test_transaction_journal_recording_and_persistence(self):
        journal = TransactionJournal(
            host_name="web01",
            play_uuid="test-uuid-1234",
            storage_dir=self.temp_storage,
        )

        undo = UndoAction(
            module="ansible.builtin.copy",
            action="restore_snapshot",
            parameters={"dest": "/etc/app.conf", "src": "/tmp/backup.1"},
        )

        entry = journal.record_mutation(
            task_name="Deploy config",
            task_uuid="t-1",
            supports_atomic=True,
            undo_action=undo,
        )

        self.assertEqual(entry.entry_id, 1)
        self.assertEqual(len(journal.entries), 1)

        # Verify disk persistence
        journal_file = os.path.join(self.temp_storage, "web01", "journal.json")
        self.assertTrue(os.path.exists(journal_file))

    def test_rollback_manager_lifo_execution(self):
        executed_undos = []

        def mock_task_runner(host: str, action: UndoAction):
            executed_undos.append((host, action.parameters["step"]))
            return {"failed": False, "changed": True}

        manager = RollbackManager(policy=RollbackPolicy.STRICT, task_runner=mock_task_runner)

        # Task 1 mutated
        manager.register_task_mutation(
            host_name="host1",
            task_name="Task 1",
            task_uuid="uuid-1",
            result={
                "changed": True,
                "_ansible_supports_atomic": True,
                "_ansible_undo": {"module": "test", "action": "undo", "parameters": {"step": 1}},
            },
        )

        # Task 2 mutated
        manager.register_task_mutation(
            host_name="host1",
            task_name="Task 2",
            task_uuid="uuid-2",
            result={
                "changed": True,
                "_ansible_supports_atomic": True,
                "_ansible_undo": {"module": "test", "action": "undo", "parameters": {"step": 2}},
            },
        )

        # Task 3 mutated
        manager.register_task_mutation(
            host_name="host1",
            task_name="Task 3",
            task_uuid="uuid-3",
            result={
                "changed": True,
                "_ansible_supports_atomic": True,
                "_ansible_undo": {"module": "test", "action": "undo", "parameters": {"step": 3}},
            },
        )

        # Trigger Rollback
        success = manager.rollback_host("host1")
        self.assertTrue(success)

        # Assert LIFO execution: 3 -> 2 -> 1
        self.assertEqual(
            executed_undos,
            [
                ("host1", 3),
                ("host1", 2),
                ("host1", 1),
            ],
        )

        recap = manager.get_recap_summary()
        self.assertEqual(recap["host1"]["mutations"], 3)
        self.assertEqual(recap["host1"]["rolled_back"], 3)
        self.assertEqual(recap["host1"]["rollback_failed"], 0)

    def test_strict_policy_rejects_non_atomic_mutation(self):
        manager = RollbackManager(policy=RollbackPolicy.STRICT)

        with self.assertRaises(UnsupportedAtomicModuleError) as ctx:
            manager.register_task_mutation(
                host_name="db01",
                task_name="Run raw migration",
                task_uuid="uuid-raw",
                result={
                    "changed": True,
                    "_ansible_supports_atomic": False,
                },
            )
        self.assertIn("does not support atomic rollback", str(ctx.exception))

    def test_best_effort_policy_skips_non_atomic_during_rollback(self):
        executed_undos = []

        def mock_task_runner(host: str, action: UndoAction):
            executed_undos.append(action.parameters["step"])
            return {"failed": False}

        manager = RollbackManager(policy=RollbackPolicy.BEST_EFFORT, task_runner=mock_task_runner)

        # Atomic Task 1
        manager.register_task_mutation(
            host_name="web02",
            task_name="Task 1",
            task_uuid="u-1",
            result={
                "changed": True,
                "_ansible_supports_atomic": True,
                "_ansible_undo": {"module": "test", "action": "undo", "parameters": {"step": 1}},
            },
        )

        # Non-atomic Task 2
        manager.register_task_mutation(
            host_name="web02",
            task_name="Task 2",
            task_uuid="u-2",
            result={
                "changed": True,
                "_ansible_supports_atomic": False,
            },
        )

        # Atomic Task 3
        manager.register_task_mutation(
            host_name="web02",
            task_name="Task 3",
            task_uuid="u-3",
            result={
                "changed": True,
                "_ansible_supports_atomic": True,
                "_ansible_undo": {"module": "test", "action": "undo", "parameters": {"step": 3}},
            },
        )

        manager.rollback_host("web02")

        # Only atomic tasks 3 and 1 were reversed
        self.assertEqual(executed_undos, [3, 1])
        recap = manager.get_recap_summary()
        self.assertEqual(recap["web02"]["mutations"], 3)
        self.assertEqual(recap["web02"]["rolled_back"], 2)
        self.assertEqual(recap["web02"]["unreverted"], 1)

    def test_checkpoint_scoped_rollback(self):
        executed_undos = []

        def mock_task_runner(host: str, action: UndoAction):
            executed_undos.append(action.parameters["step"])
            return {"failed": False}

        manager = RollbackManager(policy=RollbackPolicy.STRICT, task_runner=mock_task_runner)

        manager.register_task_mutation(
            host_name="app01",
            task_name="Task 1",
            task_uuid="u-1",
            result={
                "changed": True,
                "_ansible_supports_atomic": True,
                "_ansible_undo": {"module": "test", "action": "undo", "parameters": {"step": 1}},
            },
        )

        # Set checkpoint
        manager.register_task_mutation(
            host_name="app01",
            task_name="Task 2",
            task_uuid="u-2",
            checkpoint="cp_mid",
            result={
                "changed": True,
                "_ansible_supports_atomic": True,
                "_ansible_undo": {"module": "test", "action": "undo", "parameters": {"step": 2}},
            },
        )

        manager.register_task_mutation(
            host_name="app01",
            task_name="Task 3",
            task_uuid="u-3",
            result={
                "changed": True,
                "_ansible_supports_atomic": True,
                "_ansible_undo": {"module": "test", "action": "undo", "parameters": {"step": 3}},
            },
        )

        # Roll back only to checkpoint cp_mid (should revert 3 and 2, but keep 1)
        manager.rollback_host("app01", checkpoint="cp_mid")
        self.assertEqual(executed_undos, [3, 2])

    def test_journal_load_from_disk_and_recovery(self):
        journal = TransactionJournal(
            host_name="disk01",
            play_uuid="test-persist-uuid",
            storage_dir=self.temp_storage,
        )
        journal.record_mutation(
            task_name="Deploy app",
            task_uuid="u-persist",
            supports_atomic=True,
            undo_action=UndoAction(
                module="ansible.builtin.copy",
                action="restore",
                parameters={"path": "/etc/test"},
            ),
        )

        journal_file = os.path.join(self.temp_storage, "disk01", "journal.json")
        self.assertTrue(os.path.exists(journal_file))

        # Reload from disk
        loaded = TransactionJournal.load_from_file(journal_file)
        self.assertEqual(loaded.host_name, "disk01")
        self.assertEqual(loaded.play_uuid, "test-persist-uuid")
        self.assertEqual(len(loaded.entries), 1)
        self.assertEqual(loaded.entries[0].undo_action.module, "ansible.builtin.copy")

    def test_explicit_checkpoint_marker(self):
        executed_undos = []

        def mock_runner(host: str, action: UndoAction):
            executed_undos.append(action.parameters["id"])
            return {"failed": False}

        manager = RollbackManager(policy=RollbackPolicy.STRICT, task_runner=mock_runner)

        # Step 1
        manager.register_task_mutation(
            host_name="hostX",
            task_name="Step 1",
            task_uuid="s1",
            result={
                "changed": True,
                "_ansible_supports_atomic": True,
                "_ansible_undo": {"module": "m", "action": "a", "parameters": {"id": 1}},
            },
        )

        # Explicit Checkpoint Marker
        manager.record_checkpoint("hostX", "savepoint_alpha")

        # Step 2
        manager.register_task_mutation(
            host_name="hostX",
            task_name="Step 2",
            task_uuid="s2",
            result={
                "changed": True,
                "_ansible_supports_atomic": True,
                "_ansible_undo": {"module": "m", "action": "a", "parameters": {"id": 2}},
            },
        )

        # Rollback to savepoint_alpha
        manager.rollback_host("hostX", checkpoint="savepoint_alpha")
        self.assertEqual(executed_undos, [2])

    def test_task_executor_atomic_mixin_automatic_rollback_on_failure(self):
        from ansible.executor.rollback_manager import TaskExecutorAtomicMixin

        class MockPlayContext:
            def __init__(self, atomic=True, rollback_policy="strict"):
                self.atomic = atomic
                self.rollback_policy = rollback_policy
                self.current_checkpoint = None

        executed_undos = []

        def mock_runner(host: str, action: UndoAction):
            executed_undos.append(action.parameters["dest"])
            return {"failed": False}

        play_context = MockPlayContext(atomic=True, rollback_policy="strict")
        rollback_mgr = RollbackManager(policy=RollbackPolicy.STRICT, task_runner=mock_runner)
        executor = TaskExecutorAtomicMixin(play_context=play_context, rollback_manager=rollback_mgr)

        # 1. Successful mutating task
        res1 = executor.execute_atomic_task(
            host_name="node1",
            task_name="Copy config",
            task_uuid="t-copy",
            action_name="ansible.builtin.copy",
            task_args={"dest": "/etc/cfg1"},
            module_invoker=lambda: {
                "changed": True,
                "_ansible_supports_atomic": True,
                "_ansible_undo": {
                    "module": "ansible.builtin.copy",
                    "action": "restore",
                    "parameters": {"dest": "/etc/cfg1"},
                },
            },
        )
        self.assertTrue(res1["changed"])

        # 2. Failing validation task
        res2 = executor.execute_atomic_task(
            host_name="node1",
            task_name="Health check",
            task_uuid="t-health",
            action_name="ansible.builtin.uri",
            task_args={"url": "http://localhost/health"},
            module_invoker=lambda: {"failed": True, "msg": "Connection refused", "status_code": 500},
        )

        self.assertTrue(res2["failed"])
        self.assertTrue(res2["_ansible_rolled_back"])
        self.assertEqual(executed_undos, ["/etc/cfg1"])

    def test_strict_rollback_aborts_on_compensation_failure(self):
        def failing_runner(host: str, action: UndoAction):
            return {"failed": True, "msg": "Permission denied during compensation"}

        manager = RollbackManager(policy=RollbackPolicy.STRICT, task_runner=failing_runner)
        manager.register_task_mutation(
            host_name="hostF",
            task_name="Task Fail",
            task_uuid="tf",
            result={
                "changed": True,
                "_ansible_supports_atomic": True,
                "_ansible_undo": {"module": "m", "action": "a", "parameters": {}},
            },
        )

        with self.assertRaises(AnsibleRollbackError) as ctx:
            manager.rollback_host("hostF")
        self.assertIn("Permission denied", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
