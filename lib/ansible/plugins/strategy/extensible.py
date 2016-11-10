from ansible.playbook.task_include import TaskInclude
from ansible.playbook.block import Block
from ansible.plugins.strategy.linear import StrategyModule as LinearStrategy


def inject_tasks(blocks, parent=None):
    for idx, block in enumerate(blocks):
        if isinstance(block, Block):
            inject_tasks(block.block, parent=block)
        else:
            if not block._variable_manager:
                continue
            override = block._variable_manager.get_vars(block._loader, task=block)['ansible_override']
            if "include_after" in override and override['include_after']['task'] in block.name:
                include = override['include_after']['file']
                include_task = TaskInclude.load(
                        {'include': include},
                        block=parent,
                        variable_manager=block._variable_manager,
                        role=block._role)
                parent.block.insert(idx + 1, include_task)


class StrategyModule(LinearStrategy):
    def run(self, iterator, play_context):
        inject_tasks(iterator._blocks)
        return super(StrategyModule, self).run(iterator, play_context)
