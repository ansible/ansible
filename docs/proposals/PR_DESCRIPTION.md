### Summary

This PR introduces **Transaction Mode** (`atomic: true`), bringing native atomic execution guarantees, transactional journaling, and automated compensating rollback to Ansible playbooks.

Proposal Reference: [`docs/proposals/AEP-0082-ansible-transaction-mode.md`](https://github.com/raphgm/ansible-transaction-mode/blob/main/AEP-0082-ansible-transaction-mode.md) | Community Discussion: [raphgm/ansible-transaction-mode#1](https://github.com/raphgm/ansible-transaction-mode/issues/1)

When a multi-task play encounters an unexpected failure or validation gate failure, Ansible traditionally leaves hosts in a partially mutated state. This PR implements the **Saga / Compensating Transaction Pattern** directly within `ansible-core`:
1. Plays or blocks with `atomic: true` record an inverse compensation journal for every task that mutates state (`changed: true`).
2. Upon failure, forward execution halts and an automated, reverse-order (LIFO) compensation phase restores hosts to their baseline state.
3. Core file and system modules declare atomic capability via `supports_atomic=True` and provide exact pre-state snapshots and undo actions.
4. Non-atomic tasks are governed by configurable safety policy (`rollback_policy: strict | best_effort`).

---

### Issue Type
- [x] Feature Pull Request
- [ ] Bugfix Pull Request
- [ ] Docs Pull Request

---

### Component Name
`lib/ansible/executor/rollback_manager.py`
`lib/ansible/playbook/play_context.py`
`lib/ansible/module_utils/basic.py`

---

### Changes Included

- **Executor Engine**:
  - Implemented `RollbackManager` to supervise per-host transaction journals.
  - Implemented `TransactionJournal` with in-memory and persistent disk journal options.
  - Added `TaskExecutorAtomicMixin` with LIFO reverse-compensation dispatch on task failure.
- **PlayContext**:
  - Added `atomic` (boolean), `rollback_policy` (`strict` / `best_effort`), and `journal_storage` keywords to `PlayContext` and `TASK_ATTRIBUTE_OVERRIDES`.
- **Module Interface (`module_utils.basic`)**:
  - Added `supports_atomic` parameter to `AnsibleModule.__init__`.
  - Added `stage_file_snapshot()` and `register_undo()` methods.
  - Injected `_ansible_supports_atomic` and `_ansible_undo` into `exit_json()`.
- **CLI & Output**:
  - Enhanced play recap metrics to track `rolled_back` and `unreverted` metrics alongside `ok`, `changed`, and `failed`.
- **Tests**:
  - 9 unit tests in `test/units/executor/test_rollback_manager.py` (100% passing).
  - Integration target in `test/integration/targets/atomic_playbooks/`.
- **Documentation & Changelog**:
  - Included formal specification: `docs/proposals/AEP-0082-ansible-transaction-mode.md`.
  - Added release note fragment: `changelogs/fragments/aep-0082-transaction-mode.yml`.

---

### Example Playbook

```yaml
- name: Atomic Web Server Deployment
  hosts: webservers
  atomic: true
  rollback_policy: strict

  tasks:
    - name: 1. Deploy new application configuration
      ansible.builtin.template:
        src: app.conf.j2
        dest: /etc/nginx/conf.d/app.conf

    - name: 2. Restart NGINX
      ansible.builtin.service:
        name: nginx
        state: restarted

    - name: 3. Synthetic health verification
      ansible.builtin.uri:
        url: http://127.0.0.1/healthz
        status_code: 200
```

#### Execution Output on Failure
```text
PLAY [Atomic Web Server Deployment] *************************************************************

TASK [1. Deploy new application configuration] **************************************************
changed: [web01]

TASK [2. Restart NGINX] *************************************************************************
changed: [web01]

TASK [3. Synthetic health verification] *********************************************************
fatal: [web01]: FAILED! => {"status_code": 502, "msg": "Bad Gateway"}

ROLLBACK INITIATED [web01] **********************************************************************
<- [web01] Restored previous service state for 'nginx'
<- [web01] Restored snapshot for '/etc/nginx/conf.d/app.conf'
ROLLBACK COMPLETED [web01] **********************************************************************

PLAY RECAP **************************************************************************************
web01                      : ok=0    changed=2    rolled_back=2    unreverted=0    failed=1
```

---

### Verification & Testing
- Unit tests run via `PYTHONPATH=lib python3 -m unittest discover -s test/units/executor -p "test_rollback_manager.py"` with 9/9 passing tests.
- Tested zero regressions on non-atomic plays (`atomic: false`).

---

### Checklist
- [x] Code conforms to Ansible's Python coding style and PEP 8 guidelines.
- [x] Unit tests added and passing under `ansible-test units`.
- [x] Integration tests added under `ansible-test integration`.
- [x] Documentation and schema specifications added (`AEP-0082`).
- [x] Changelog fragment added under `changelogs/fragments/aep-0082-transaction-mode.yml`.
