# -*- coding: utf-8 -*-

# Copyright: (c) 2016, Matt Davis, <mdavis@ansible.com>
# Copyright: (c) 2016, Chris Houseknecht, <house@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment(object):

    # Azure doc fragment
    DOCUMENTATION = r'''
options:
    tags:
        description:
            - Dictionary of string:string pairs to assign as metadata to the object.
            - Metadata tags on the object will be updated with any provided values.
            - To remove tags set append_tags option to false.
        type: dict
    append_tags:
        description:
            - Use to control if tags field is canonical or just appends to existing tags.
            - When canonical, any tags not found in the tags parameter will be removed from the object's metadata.
        type: bool
        default: yes
    '''
