#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The iosxr_static_routes class
It is in this file where the current configuration (as dict)
is compared to the provided configuration (as dict) and the command set
necessary to bring the current configuration to it's desired end-state is
created
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from ansible.module_utils.network.common.cfg.base import ConfigBase
from ansible.module_utils.network.common.utils import to_list
from ansible.module_utils.network.iosxr.facts.facts import Facts
from ansible.module_utils.six import iteritems
from ansible.module_utils.network.common.utils import (
    search_obj_in_list,
    remove_empties,
    dict_diff,
    dict_merge,
)


class Static_routes(ConfigBase):
    """
    The iosxr_static_routes class
    """

    gather_subset = [
        "!all",
        "!min",
    ]

    gather_network_resources = [
        "static_routes",
    ]

    def __init__(self, module):
        super(Static_routes, self).__init__(module)

    def get_static_routes_facts(self, data=None):
        """ Get the 'facts' (the current configuration)

        :rtype: A dictionary
        :returns: The current configuration as a dictionary
        """
        facts, _warnings = Facts(self._module).get_facts(
            self.gather_subset, self.gather_network_resources, data=data
        )
        static_routes_facts = facts["ansible_network_resources"].get("static_routes")
        if not static_routes_facts:
            return []
        return static_routes_facts

    def execute_module(self):
        """ Execute the module

        :rtype: A dictionary
        :returns: The result from module execution
        """
        result = {"changed": False}
        warnings = list()
        commands = list()

        if self.state in self.ACTION_STATES:
            existing_static_routes_facts = self.get_static_routes_facts()
        else:
            existing_static_routes_facts = []

        if self.state in self.ACTION_STATES or self.state == "rendered":
            commands.extend(self.set_config(existing_static_routes_facts))

        if commands and self.state in self.ACTION_STATES:
            if not self._module.check_mode:
                self._connection.edit_config(commands)
            result["changed"] = True

        if self.state in self.ACTION_STATES:
            result["commands"] = commands

        if self.state in self.ACTION_STATES or self.state == "gathered":
            changed_static_routes_facts = self.get_static_routes_facts()

        elif self.state == "rendered":
            result["rendered"] = commands

        elif self.state == "parsed":
            running_config = self._module.params["running_config"]
            if not running_config:
                self._module.fail_json(
                    msg="value of running_config parameter must not be empty for state parsed"
                )
            result["parsed"] = self.get_static_routes_facts(data=running_config)

        if self.state in self.ACTION_STATES:
            result["before"] = existing_static_routes_facts
            if result["changed"]:
                result["after"] = changed_static_routes_facts

        elif self.state == "gathered":
            result["gathered"] = changed_static_routes_facts

        result["warnings"] = warnings
        return result

    def set_config(self, existing_static_routes_facts):
        """ Collect the configuration from the args passed to the module,
            collect the current configuration (as a dict from facts)

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        want = self._module.params["config"]
        have = existing_static_routes_facts
        resp = self.set_state(want, have)
        return to_list(resp)

    def set_state(self, want, have):
        """ Select the appropriate function based on the state provided

        :param want: the desired configuration as a dictionary
        :param have: the current configuration as a dictionary
        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        state = self._module.params["state"]
        commands = []

        if state in ("overridden", "merged", "replaced", "rendered") and not want:
            self._module.fail_json(
                msg="value of config parameter must not be empty for state {0}".format(
                    state
                )
            )

        if state == "overridden":
            commands.extend(self._state_overridden(want, have))

        elif state == "deleted":
            if not want:
                if len(have) >= 1:
                    return "no router static"

            else:
                for w_item in want:
                    obj_in_have = self._find_vrf(w_item, have)
                    if obj_in_have:
                        commands.extend(
                            self._state_deleted(remove_empties(w_item), obj_in_have)
                        )

        else:
            for w_item in want:
                obj_in_have = self._find_vrf(w_item, have)
                if state == "merged" or self.state == "rendered":
                    commands.extend(
                        self._state_merged(remove_empties(w_item), obj_in_have)
                    )

                elif state == "replaced":
                    commands.extend(
                        self._state_replaced(remove_empties(w_item), obj_in_have)
                    )

        if commands:
            commands.insert(0, "router static")

        return commands

    def _state_replaced(self, want, have):
        """ The command generator when state is replaced

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []

        for want_afi in want.get("address_families", []):
            have_afi = (
                self.find_af_context(want_afi, have.get("address_families", [])) or {}
            )
            update_commands = []
            for want_route in want_afi.get("routes", []):
                have_route = (
                    search_obj_in_list(
                        want_route["dest"], have_afi.get("routes", []), key="dest"
                    )
                    or {}
                )

                rotated_have_next_hops = self.rotate_next_hops(
                    have_route.get("next_hops", {})
                )
                rotated_want_next_hops = self.rotate_next_hops(
                    want_route.get("next_hops", {})
                )

                for key in rotated_have_next_hops.keys():
                    if key not in rotated_want_next_hops:
                        cmd = "no {0}".format(want_route["dest"])
                        for item in key:
                            if "." in item or ":" in item or "/" in item:
                                cmd += " {0}".format(item)
                            else:
                                cmd += " vrf {0}".format(item)
                        update_commands.append(cmd)

                for key, value in iteritems(rotated_want_next_hops):
                    if key in rotated_have_next_hops:
                        existing = True
                        have_exit_point_attribs = rotated_have_next_hops[key]

                    else:
                        existing = False
                        have_exit_point_attribs = {}

                    updates = dict_diff(have_exit_point_attribs, value)

                    if updates or not existing:
                        update_commands.append(
                            self._compute_commands(
                                dest=want_route["dest"], next_hop=key, updates=updates
                            )
                        )

            if update_commands:
                update_commands.insert(
                    0,
                    "address-family {0} {1}".format(want_afi["afi"], want_afi["safi"]),
                )
                commands.extend(update_commands)

        if "vrf" in want and update_commands:
            commands.insert(0, "vrf {0}".format(want["vrf"]))

        return commands

    def _state_overridden(self, want, have):
        """ The command generator when state is overridden

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []

        # Iterate through all the entries, i.e., VRFs and Global entry in have
        # and fully remove the ones that are not present in want and then call
        # replaced

        for h_item in have:
            w_item = self._find_vrf(h_item, want)

            # Delete all the top-level keys (VRFs/Global Route Entry) that are
            # not specified in want.
            if not w_item:
                if "vrf" in h_item:
                    commands.append("no vrf {0}".format(h_item["vrf"]))
                else:
                    for have_afi in h_item.get("address_families", []):
                        commands.append(
                            "no address-family {0} {1}".format(
                                have_afi["afi"], have_afi["safi"]
                            )
                        )

            # For VRFs/Global Entry present in want, we also need to delete extraneous routes
            # from them. We cannot reuse `_state_replaced` for this purpose since its scope is
            # limited to replacing a single `dest`.
            else:
                del_cmds = []
                for have_afi in h_item.get("address_families", []):
                    want_afi = (
                        self.find_af_context(
                            have_afi, w_item.get("address_families", [])
                        )
                        or {}
                    )
                    update_commands = []
                    for h_route in have_afi.get("routes", []):
                        w_route = (
                            search_obj_in_list(
                                h_route["dest"], want_afi.get("routes", []), key="dest"
                            )
                            or {}
                        )
                        if not w_route:
                            update_commands.append("no {0}".format(h_route["dest"]))

                    if update_commands:
                        update_commands.insert(
                            0,
                            "address-family {0} {1}".format(
                                want_afi["afi"], want_afi["safi"]
                            ),
                        )
                        del_cmds.extend(update_commands)

                if "vrf" in want and update_commands:
                    del_cmds.insert(0, "vrf {0}".format(want["vrf"]))

                commands.extend(del_cmds)

        # We finally call `_state_replaced` to replace exiting `dest` entries
        # or add new ones as specified in want.
        for w_item in want:
            h_item = self._find_vrf(w_item, have)
            commands.extend(self._state_replaced(remove_empties(w_item), h_item))

        return commands

    def _state_merged(self, want, have):
        """ The command generator when state is merged

        :rtype: A list
        :returns: the commands necessary to merge the provided into
                  the current configuration
        """
        commands = []

        for want_afi in want.get("address_families", []):
            have_afi = (
                self.find_af_context(want_afi, have.get("address_families", [])) or {}
            )

            update_commands = []
            for want_route in want_afi.get("routes", []):
                have_route = (
                    search_obj_in_list(
                        want_route["dest"], have_afi.get("routes", []), key="dest"
                    )
                    or {}
                )

                # convert the next_hops list of dictionaries to dictionary of
                # dictionaries with (`dest_vrf`, `forward_router_address`, `interface`) tuple
                # being the key for each dictionary.
                # a combination of these 3 attributes uniquely identifies a route entry.
                # in case `dest_vrf` is not specified, `forward_router_address` and `interface`
                # become the unique identifier
                rotated_have_next_hops = self.rotate_next_hops(
                    have_route.get("next_hops", {})
                )
                rotated_want_next_hops = self.rotate_next_hops(
                    want_route.get("next_hops", {})
                )

                # for every dict in the want next_hops dictionaries, if the key
                # is present in `rotated_have_next_hops`, we set `existing` to True,
                # which means the the given want exit point exists and we run dict_diff
                # on `value` which is basically all the other attributes of the exit point
                # if the key is not present, it means that this is a new exit point
                for key, value in iteritems(rotated_want_next_hops):
                    if key in rotated_have_next_hops:
                        existing = True
                        have_exit_point_attribs = rotated_have_next_hops[key]

                    else:
                        existing = False
                        have_exit_point_attribs = {}

                    updates = dict_diff(have_exit_point_attribs, value)
                    if updates or not existing:
                        update_commands.append(
                            self._compute_commands(
                                dest=want_route["dest"],
                                next_hop=key,
                                # dict_merge() is necessary to make sure that we
                                # don't end up overridding the entry and also to
                                # allow incremental updates
                                updates=dict_merge(
                                    rotated_have_next_hops.get(key, {}), updates
                                ),
                            )
                        )

            if update_commands:
                update_commands.insert(
                    0,
                    "address-family {0} {1}".format(want_afi["afi"], want_afi["safi"]),
                )
                commands.extend(update_commands)

        if "vrf" in want and update_commands:
            commands.insert(0, "vrf {0}".format(want["vrf"]))

        return commands

    def _state_deleted(self, want, have):
        """ The command generator when state is deleted

        :rtype: A list
        :returns: the commands necessary to remove the current configuration
                  of the provided objects
        """
        commands = []
        if "address_families" not in want:
            return ["no vrf {0}".format(want["vrf"])]

        else:
            for want_afi in want.get("address_families", []):
                update_commands = []
                have_afi = (
                    self.find_af_context(want_afi, have.get("address_families", []))
                    or {}
                )
                if have_afi:
                    if "routes" not in want_afi:
                        commands.append(
                            "no address-family {0} {1}".format(
                                have_afi["afi"], have_afi["safi"]
                            )
                        )
                    else:
                        for want_route in want_afi.get("routes", []):
                            have_route = (
                                search_obj_in_list(
                                    want_route["dest"],
                                    have_afi.get("routes", []),
                                    key="dest",
                                )
                                or {}
                            )
                            if have_route:
                                if "next_hops" not in want_route:
                                    update_commands.append(
                                        "no {0}".format(want_route["dest"])
                                    )
                                else:
                                    rotated_have_next_hops = self.rotate_next_hops(
                                        have_route.get("next_hops", {})
                                    )
                                    rotated_want_next_hops = self.rotate_next_hops(
                                        want_route.get("next_hops", {})
                                    )

                                    for key in rotated_want_next_hops.keys():
                                        if key in rotated_have_next_hops:
                                            cmd = "no {0}".format(want_route["dest"])
                                            for item in key:
                                                if (
                                                    "." in item
                                                    or ":" in item
                                                    or "/" in item
                                                ):
                                                    cmd += " {0}".format(item)
                                                else:
                                                    cmd += " vrf {0}".format(item)
                                            update_commands.append(cmd)

                        if update_commands:
                            update_commands.insert(
                                0,
                                "address-family {0} {1}".format(
                                    want_afi["afi"], want_afi["safi"]
                                ),
                            )
                            commands.extend(update_commands)

            if "vrf" in want and commands:
                commands.insert(0, "vrf {0}".format(want["vrf"]))

        return commands

    def _find_vrf(self, item, entries):
        """ This method iterates through the items
            in `entries` and returns the object that
            matches `item`.

        :rtype: A dict
        :returns: the obj in `entries` that matches `item`
        """
        obj = {}
        afi = item.get("vrf")

        if afi:
            obj = search_obj_in_list(afi, entries, key="vrf") or {}
        else:
            for x in entries:
                if "vrf" not in remove_empties(x):
                    obj = x
                    break
        return obj

    def find_af_context(self, want_af_context, have_address_families):
        """ This method iterates through the have AFs
            and returns the one that matches the want AF

        :rtype: A dict
        :returns: the corresponding AF in have AFs
                  that matches the want AF
        """
        for have_af in have_address_families:
            if (
                have_af["afi"] == want_af_context["afi"]
                and have_af["safi"] == want_af_context["safi"]
            ):
                return have_af

    def rotate_next_hops(self, next_hops):
        """ This method iterates through the list of
            next hops for a given destination network
            and converts it to a dictionary of dictionaries.
            Each dictionary has a primary key indicated by the
            tuple of `dest_vrf`, `forward_router_address` and
            `interface` and the value of this key is a dictionary
            that contains all the other attributes of the next hop.

        :rtype: A dict
        :returns: A next_hops list in a dictionary of dictionaries format
        """
        next_hops_dict = {}

        for entry in next_hops:
            entry = entry.copy()
            key_list = []

            for x in ["dest_vrf", "forward_router_address", "interface"]:
                if entry.get(x):
                    key_list.append(entry.pop(x))

            key = tuple(key_list)
            next_hops_dict[key] = entry

        return next_hops_dict

    def _compute_commands(self, dest, next_hop, updates=None):
        """ This method computes a static route entry command
            from the specified `dest`, `next_hop` and `updates`

        :rtype: A str
        :returns: A platform specific static routes command
        """
        if not updates:
            updates = {}

        command = dest

        for x in next_hop:
            if "." in x or ":" in x or "/" in x:
                command += " {0}".format(x)
            else:
                command += " vrf {0}".format(x)

        for key in sorted(updates):
            if key == "admin_distance":
                command += " {0}".format(updates[key])
            else:
                command += " {0} {1}".format(key, updates[key])

        return command
