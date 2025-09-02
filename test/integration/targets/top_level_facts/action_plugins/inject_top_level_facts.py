from __future__ import annotations


from ansible.plugins.action import ActionBase


class ActionModule(ActionBase):
    def run(self, tmp=None, task_vars=None):
        result = super().run(task_vars=task_vars)

        result['ansible_facts'] = {
            'old_top_level_fact': 'deprecated',
            'old_top_level_fact_not_overwritten': 'deprecated_not_overwritten',
        }

        v = self._task.args.get('v', '')
        self.set_top_level_facts(
            **{
                f'top_level_fact{v}': f'hello{v}',
                'old_top_level_fact': 'overwritten',  # overwrites the deprecated one
            }
        )

        return result
