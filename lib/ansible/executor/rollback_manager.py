# (c) 2026 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import enum
import json
import logging
import os
import shutil
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("ansible.executor.rollback_manager")


class RollbackPolicy(str, enum.Enum):
    STRICT = "strict"
    BEST_EFFORT = "best_effort"


class TransactionStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    COMMITTED = "COMMITTED"
    ROLLING_BACK = "ROLLING_BACK"
    ROLLED_BACK = "ROLLED_BACK"
    ROLLBACK_FAILED = "ROLLBACK_FAILED"


class AnsibleRollbackError(Exception):
    """Raised when a compensating rollback action encounters an unrecoverable failure."""
    pass


class UnsupportedAtomicModuleError(Exception):
    """Raised in strict policy mode when a mutating task runs a module without atomic support."""
    pass


@dataclass
class UndoAction:
    module: str
    action: str
    parameters: Dict[str, Any]
    requires_become: bool = False
    become_user: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> UndoAction:
        return cls(**data)


@dataclass
class JournalEntry:
    entry_id: int
    task_name: str
    task_uuid: str
    timestamp: str
    supports_atomic: bool
    undo_action: Optional[UndoAction]
    checkpoint: Optional[str] = None
    applied_successfully: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "task_name": self.task_name,
            "task_uuid": self.task_uuid,
            "timestamp": self.timestamp,
            "supports_atomic": self.supports_atomic,
            "undo_action": self.undo_action.to_dict() if self.undo_action else None,
            "checkpoint": self.checkpoint,
            "applied_successfully": self.applied_successfully,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> JournalEntry:
        undo_raw = data.get("undo_action")
        undo_action = UndoAction.from_dict(undo_raw) if undo_raw else None
        return cls(
            entry_id=data["entry_id"],
            task_name=data["task_name"],
            task_uuid=data["task_uuid"],
            timestamp=data["timestamp"],
            supports_atomic=data["supports_atomic"],
            undo_action=undo_action,
            checkpoint=data.get("checkpoint"),
            applied_successfully=data.get("applied_successfully", True),
        )


class TransactionJournal:
    """Maintains the chronological sequence of state mutations for a specific host."""

    def __init__(self, host_name: str, play_uuid: str, storage_dir: Optional[str] = None):
        self.host_name = host_name
        self.play_uuid = play_uuid
        self.version = "1.0"
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.status = TransactionStatus.ACTIVE
        self.entries: List[JournalEntry] = []
        self._next_id = 1
        self.storage_dir = storage_dir or f"/tmp/.ansible_journal_{play_uuid}"
        self.staging_dir = os.path.join(self.storage_dir, host_name)

    def record_mutation(
        self,
        task_name: str,
        task_uuid: str,
        supports_atomic: bool,
        undo_action: Optional[UndoAction],
        checkpoint: Optional[str] = None,
    ) -> JournalEntry:
        """Appends a mutating step to the journal."""
        entry = JournalEntry(
            entry_id=self._next_id,
            task_name=task_name,
            task_uuid=task_uuid,
            timestamp=datetime.now(timezone.utc).isoformat(),
            supports_atomic=supports_atomic,
            undo_action=undo_action,
            checkpoint=checkpoint,
        )
        self._next_id += 1
        self.entries.append(entry)
        self._persist()
        return entry

    def get_entries_since_checkpoint(self, checkpoint: Optional[str] = None) -> List[JournalEntry]:
        """Returns entries to rollback, either all or up to a specific checkpoint."""
        if not checkpoint:
            return list(reversed(self.entries))

        reversed_list = []
        found = False
        for entry in reversed(self.entries):
            reversed_list.append(entry)
            if entry.checkpoint == checkpoint:
                found = True
                break
        if not found:
            raise ValueError(f"Checkpoint '{checkpoint}' not found in host journal {self.host_name}")
        return reversed_list

    def record_checkpoint(self, name: str, task_name: str = "Checkpoint", task_uuid: str = "") -> JournalEntry:
        """Records an explicit transaction savepoint marker in the journal."""
        entry = JournalEntry(
            entry_id=self._next_id,
            task_name=f"Checkpoint: {name}",
            task_uuid=task_uuid or str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc).isoformat(),
            supports_atomic=True,
            undo_action=None,
            checkpoint=name,
        )
        self._next_id += 1
        self.entries.append(entry)
        self._persist()
        return entry

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "play_uuid": self.play_uuid,
            "host": self.host_name,
            "created_at": self.created_at,
            "status": self.status.value,
            "entries": [e.to_dict() for e in self.entries],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], storage_dir: Optional[str] = None) -> TransactionJournal:
        journal = cls(
            host_name=data["host"],
            play_uuid=data["play_uuid"],
            storage_dir=storage_dir,
        )
        journal.version = data.get("version", "1.0")
        journal.created_at = data.get("created_at", datetime.now(timezone.utc).isoformat())
        journal.status = TransactionStatus(data.get("status", TransactionStatus.ACTIVE.value))
        journal.entries = [JournalEntry.from_dict(e) for e in data.get("entries", [])]
        if journal.entries:
            journal._next_id = max(e.entry_id for e in journal.entries) + 1
        return journal

    @classmethod
    def load_from_file(cls, file_path: str) -> TransactionJournal:
        """Loads a persisted journal from disk."""
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        storage_dir = os.path.dirname(os.path.dirname(os.path.abspath(file_path)))
        return cls.from_dict(data, storage_dir=storage_dir)

    def _persist(self) -> None:
        """Saves current journal state to disk for crash resilience."""
        try:
            os.makedirs(self.staging_dir, exist_ok=True)
            journal_file = os.path.join(self.staging_dir, "journal.json")
            with open(journal_file, "w", encoding="utf-8") as f:
                json.dump(self.to_dict(), f, indent=2)
        except OSError as e:
            logger.warning(f"Failed to persist journal for {self.host_name}: {e}")

    def purge_storage(self) -> None:
        """Cleans up staging directory on successful transaction commit."""
        if os.path.exists(self.staging_dir):
            shutil.rmtree(self.staging_dir, ignore_errors=True)


class RollbackManager:
    """
    Coordinates atomic transactions across all hosts in a Playbook.
    Manages journal persistence, failure interception, LIFO compensation, and recap metrics.
    """

    def __init__(
        self,
        play_uuid: Optional[str] = None,
        policy: RollbackPolicy = RollbackPolicy.STRICT,
        task_runner: Optional[Callable[[str, UndoAction], Dict[str, Any]]] = None,
    ):
        self.play_uuid = play_uuid or str(uuid.uuid4())
        self.policy = policy
        self.journals: Dict[str, TransactionJournal] = {}
        self.task_runner = task_runner  # Injected delegate for dispatching reverse tasks
        self.recap_metrics: Dict[str, Dict[str, int]] = {}

    def get_or_create_journal(self, host_name: str) -> TransactionJournal:
        if host_name not in self.journals:
            self.journals[host_name] = TransactionJournal(host_name, self.play_uuid)
            self.recap_metrics[host_name] = {
                "mutations": 0,
                "rolled_back": 0,
                "unreverted": 0,
                "rollback_failed": 0,
            }
        return self.journals[host_name]

    def register_task_mutation(
        self,
        host_name: str,
        task_name: str,
        task_uuid: str,
        result: Dict[str, Any],
        checkpoint: Optional[str] = None,
    ) -> Optional[JournalEntry]:
        """Examines module execution result; if mutated, registers journal entry."""
        if not result.get("changed", False):
            return None

        journal = self.get_or_create_journal(host_name)
        supports_atomic = result.get("_ansible_supports_atomic", False)
        undo_data = result.get("_ansible_undo")

        if not supports_atomic:
            if self.policy == RollbackPolicy.STRICT:
                raise UnsupportedAtomicModuleError(
                    f"Task '{task_name}' on host '{host_name}' mutated state but module does not "
                    f"support atomic rollback (policy=strict)."
                )
            logger.warning(
                f"Task '{task_name}' on host '{host_name}' has no rollback support (policy=best_effort)."
            )

        undo_action = UndoAction.from_dict(undo_data) if undo_data else None
        entry = journal.record_mutation(
            task_name=task_name,
            task_uuid=task_uuid,
            supports_atomic=supports_atomic,
            undo_action=undo_action,
            checkpoint=checkpoint,
        )
        self.recap_metrics[host_name]["mutations"] += 1
        return entry

    def record_checkpoint(self, host_name: str, checkpoint_name: str) -> JournalEntry:
        """Records an explicit transaction savepoint for a given host."""
        journal = self.get_or_create_journal(host_name)
        return journal.record_checkpoint(name=checkpoint_name)

    def rollback_host(
        self,
        host_name: str,
        checkpoint: Optional[str] = None,
    ) -> bool:
        """
        Executes LIFO compensating actions for a specific host.
        Returns True if all reversible entries were rolled back successfully.
        """
        if host_name not in self.journals:
            return True

        journal = self.journals[host_name]
        journal.status = TransactionStatus.ROLLING_BACK
        entries_to_revert = journal.get_entries_since_checkpoint(checkpoint)

        success = True
        for entry in entries_to_revert:
            if not entry.supports_atomic or not entry.undo_action:
                logger.warning(
                    f"[{host_name}] Cannot roll back non-atomic entry #{entry.entry_id}: {entry.task_name}"
                )
                self.recap_metrics[host_name]["unreverted"] += 1
                continue

            logger.info(
                f"[{host_name}] Reverting entry #{entry.entry_id}: {entry.task_name} via {entry.undo_action.module}"
            )

            try:
                if self.task_runner:
                    res = self.task_runner(host_name, entry.undo_action)
                    if res.get("failed", False):
                        raise AnsibleRollbackError(res.get("msg", "Unknown error during compensation"))
                self.recap_metrics[host_name]["rolled_back"] += 1
            except Exception as e:
                logger.error(
                    f"[{host_name}] Rollback failed for entry #{entry.entry_id} ({entry.task_name}): {e}"
                )
                self.recap_metrics[host_name]["rollback_failed"] += 1
                journal.status = TransactionStatus.ROLLBACK_FAILED
                success = False
                if self.policy == RollbackPolicy.STRICT:
                    raise AnsibleRollbackError(
                        f"Strict rollback aborted on host {host_name} at entry #{entry.entry_id}: {e}"
                    ) from e

        if success:
            journal.status = TransactionStatus.ROLLED_BACK
        return success

    def commit(self, host_name: Optional[str] = None) -> None:
        """Commits transaction and purges temporary backup journals."""
        hosts = [host_name] if host_name else list(self.journals.keys())
        for h in hosts:
            if h in self.journals:
                self.journals[h].status = TransactionStatus.COMMITTED
                self.journals[h].purge_storage()

    def get_recap_summary(self) -> Dict[str, Dict[str, int]]:
        return self.recap_metrics


class TaskExecutorAtomicMixin:
    """
    Mixin integrated into TaskExecutor governing atomic transaction tracking
    and automated compensation upon task failure.
    """

    def __init__(
        self,
        play_context: Any,
        rollback_manager: Optional[RollbackManager] = None,
        **kwargs: Any,
    ) -> None:
        self._play_context = play_context
        self._rollback_manager = rollback_manager or RollbackManager(
            policy=RollbackPolicy(getattr(play_context, "rollback_policy", "strict"))
        )

    @property
    def rollback_manager(self) -> RollbackManager:
        return self._rollback_manager

    def execute_atomic_task(
        self,
        host_name: str,
        task_name: str,
        task_uuid: str,
        action_name: str,
        task_args: Dict[str, Any],
        module_invoker: Callable[[], Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Executes a task under atomic transaction semantics:
        1. Handles explicit transaction control tasks ('checkpoint', 'rollback_to').
        2. Dispatches task execution via module_invoker.
        3. If mutation occurred ('changed'=True), records entry in host transaction journal.
        4. If failure occurred ('failed'=True), automatically initiates rollback compensation.
        """
        is_atomic = getattr(self._play_context, "atomic", False)

        if action_name in ("ansible.builtin.checkpoint", "checkpoint"):
            checkpoint_name = task_args.get("name", "checkpoint")
            self._rollback_manager.record_checkpoint(host_name, checkpoint_name)
            return {
                "changed": False,
                "msg": f"Transaction checkpoint '{checkpoint_name}' established for {host_name}",
            }

        if action_name in ("ansible.builtin.rollback_to", "rollback_to"):
            target_checkpoint = task_args.get("checkpoint")
            success = self._rollback_manager.rollback_host(host_name, checkpoint=target_checkpoint)
            return {
                "changed": True,
                "rolled_back": True,
                "success": success,
                "msg": f"Rolled back to checkpoint '{target_checkpoint}' for {host_name}",
            }

        try:
            result = module_invoker()
        except Exception as e:
            result = {"failed": True, "msg": str(e), "exception": repr(e)}

        if not is_atomic:
            return result

        if result.get("changed", False):
            checkpoint_tag = getattr(self._play_context, "current_checkpoint", None)
            self._rollback_manager.register_task_mutation(
                host_name=host_name,
                task_name=task_name,
                task_uuid=task_uuid,
                result=result,
                checkpoint=checkpoint_tag,
            )

        if result.get("failed", False):
            logger.error(
                f"Task '{task_name}' failed on host '{host_name}'. Initiating compensating rollback."
            )
            rollback_ok = self._rollback_manager.rollback_host(host_name)
            result["_ansible_rolled_back"] = rollback_ok
            result["_ansible_transaction_recap"] = self._rollback_manager.get_recap_summary().get(host_name)

        return result
