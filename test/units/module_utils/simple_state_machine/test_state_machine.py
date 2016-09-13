# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

# Make coding more python3-ish
from __future__ import (absolute_import, division)
__metaclass__ = type

import os

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import patch, call
from ansible.module_utils.simple_state_machine \
    import create_events, create_states, StateMachine, TransitionError


class TestStateMachineWithValidInitialization(unittest.TestCase):

    # =======
    # HELPERS
    # =======

    @property
    def events(self):
        if not hasattr(self, '_events'):
            self._events = create_events('one',
                                         'two',
                                         'three',
                                         'four',
                                         'ninetynine')
        return self._events

    @property
    def states(self):
        if not hasattr(self, '_states'):
            self._states = create_states('one',
                                         'two',
                                         'three',
                                         'four')
        return self._states

    @property
    def starting_state(self):
        return self.states.one

    @property
    def transitions(self):
        return {
            (self.states.one, self.events.one):
                (self.states.two, self.action1),
            (self.states.one, self.events.two):
                (self.states.three, self.action2),
            (self.states.two, self.events.three):
                (self.states.four, self.action3)
        }

    def action1(self):
        pass

    def action2(self):
        pass

    def action3(self):
        pass

    # ==============
    # SETUP/TEARDOWN
    # ==============

    def setUp(self):
        self.subject = StateMachine(self.transitions,
                                    self.starting_state,
                                    self.action1)

    # =====
    # TESTS
    # =====

    @patch('ansible.module_utils.simple_state_machine.graphviz', autospec=True)
    def test_render(self, graphviz_cls):
        graph = graphviz_cls.Digraph.return_value

        path = '/tmp/state_machine_visual_3e18676'

        self.subject.render(path)

        self.assertEqual(graph.render.call_count, 1)
        self.assertEqual(graph.render.call_args, call(path))

    def test_send_event(self):
        # Double check that we are at the correct state
        self.assertEqual(self.starting_state, self.subject.state)

        action = self.subject.send_event(self.events.two)

        self.assertEqual(self.action2, action)
        self.assertEqual(self.states.three, self.subject.state)

    def test_send_event_multiple_transitions(self):
        # Double check that we are at the correct state
        self.assertEqual(self.starting_state, self.subject.state)

        self.subject.send_event(self.events.one)
        action = self.subject.send_event(self.events.three)

        self.assertEqual(self.action3, action)
        self.assertEqual(self.states.four, self.subject.state)

    def test_send_event_invalid_event(self):
        # Double check that we are at the correct state
        self.assertEqual(self.starting_state, self.subject.state)

        with self.assertRaises(TransitionError):
            self.subject.send_event(self.events.ninetynine)

        self.assertEqual(self.states.one, self.subject.state)

    def test_state(self):
        self.assertEqual(self.starting_state, self.subject.state)
