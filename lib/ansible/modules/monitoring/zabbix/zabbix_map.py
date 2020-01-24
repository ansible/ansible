#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017-2018, Antony Alekseyev <antony.alekseyev@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: zabbix_map
author:
    - "Antony Alekseyev (@Akint)"
short_description: Create/update/delete Zabbix maps
description:
    - "This module allows you to create, modify and delete Zabbix map entries,
      using Graphviz binaries and text description written in DOT language.
      Nodes of the graph will become map elements and edges will become links between map elements.
      See U(https://en.wikipedia.org/wiki/DOT_(graph_description_language)) and U(https://www.graphviz.org/) for details.
      Inspired by U(http://blog.zabbix.com/maps-for-the-lazy/)."
    - "The following extra node attributes are supported:
        C(zbx_host) contains name of the host in Zabbix. Use this if desired type of map element is C(host).
        C(zbx_group) contains name of the host group in Zabbix. Use this if desired type of map element is C(host group).
        C(zbx_map) contains name of the map in Zabbix. Use this if desired type of map element is C(map).
        C(zbx_label) contains label of map element.
        C(zbx_image) contains name of the image used to display the element in default state.
        C(zbx_image_disabled) contains name of the image used to display disabled map element.
        C(zbx_image_maintenance) contains name of the image used to display map element in maintenance.
        C(zbx_image_problem) contains name of the image used to display map element with problems.
        C(zbx_url) contains map element URL in C(name:url) format.
            More than one URL could be specified by adding a postfix (e.g., C(zbx_url1), C(zbx_url2))."
    - "The following extra link attributes are supported:
        C(zbx_draw_style) contains link line draw style. Possible values: C(line), C(bold), C(dotted), C(dashed).
        C(zbx_trigger) contains name of the trigger used as a link indicator in C(host_name:trigger_name) format.
            More than one trigger could be specified by adding a postfix (e.g., C(zbx_trigger1), C(zbx_trigger2)).
        C(zbx_trigger_color) contains indicator color specified either as CSS3 name or as a hexadecimal code starting with C(#).
        C(zbx_trigger_draw_style) contains indicator draw style. Possible values are the same as for C(zbx_draw_style)."
requirements:
    - "python >= 2.6"
    - "zabbix-api >= 0.5.4"
    - pydotplus
    - webcolors
    - Pillow
    - Graphviz
version_added: "2.8"
options:
    name:
        description:
            - Name of the map.
        required: true
        aliases: [ "map_name" ]
        type: str
    data:
        description:
            - Graph written in DOT language.
        required: false
        aliases: [ "dot_data" ]
        type: str
    state:
        description:
            - State of the map.
            - On C(present), it will create if map does not exist or update the map if the associated data is different.
            - On C(absent) will remove the map if it exists.
        required: false
        choices: ['present', 'absent']
        default: "present"
        type: str
    width:
        description:
            - Width of the map.
        required: false
        default: 800
        type: int
    height:
        description:
            - Height of the map.
        required: false
        default: 600
        type: int
    margin:
        description:
            - Size of white space between map's borders and its elements.
        required: false
        default: 40
        type: int
    expand_problem:
        description:
            - Whether the problem trigger will be displayed for elements with a single problem.
        required: false
        type: bool
        default: true
    highlight:
        description:
            - Whether icon highlighting is enabled.
        required: false
        type: bool
        default: true
    label_type:
        description:
            - Map element label type.
        required: false
        choices: ['label', 'ip', 'name', 'status', 'nothing', 'custom']
        default: "name"
        type: str
    default_image:
        description:
            - Name of the Zabbix image used to display the element if this element doesn't have the C(zbx_image) attribute defined.
        required: false
        aliases: [ "image" ]
        type: str

extends_documentation_fragment:
    - zabbix
'''

RETURN = r''' # '''

EXAMPLES = r'''
###
### Example inventory:
# [web]
# web[01:03].example.com ansible_host=127.0.0.1
# [db]
# db.example.com ansible_host=127.0.0.1
# [backup]
# backup.example.com ansible_host=127.0.0.1
###
### Each inventory host is present in Zabbix with a matching name.
###
### Contents of 'map.j2':
# digraph G {
#     graph [layout=dot splines=false overlap=scale]
#     INTERNET [zbx_url="Google:https://google.com" zbx_image="Cloud_(96)"]
# {% for web_host in groups.web %}
#     {% set web_loop = loop %}
#     web{{ '%03d' % web_loop.index }} [zbx_host="{{ web_host }}"]
#     INTERNET -> web{{ '%03d' % web_loop.index }} [zbx_trigger="{{ web_host }}:Zabbix agent on {HOST.NAME} is unreachable for 5 minutes"]
#     {% for db_host in groups.db %}
#       {% set db_loop = loop %}
#     web{{ '%03d' % web_loop.index }} -> db{{ '%03d' % db_loop.index }}
#     {% endfor %}
# {% endfor %}
#     { rank=same
# {% for db_host in groups.db %}
#     {% set db_loop = loop %}
#     db{{ '%03d' % db_loop.index }} [zbx_host="{{ db_host }}"]
#     {% for backup_host in groups.backup %}
#         {% set backup_loop = loop %}
#         db{{ '%03d' % db_loop.index }} -> backup{{ '%03d' % backup_loop.index }} [color="blue"]
#     {% endfor %}
# {% endfor %}
# {% for backup_host in groups.backup %}
#     {% set backup_loop = loop %}
#         backup{{ '%03d' % backup_loop.index }} [zbx_host="{{ backup_host }}"]
# {% endfor %}
#     }
# }
###
### Create Zabbix map "Demo Map" made of template 'map.j2'
- name: Create Zabbix map
  zabbix_map:
    server_url: http://zabbix.example.com
    login_user: username
    login_password: password
    name: Demo map
    state: present
    data: "{{ lookup('template', 'map.j2') }}"
    default_image: Server_(64)
    expand_problem: no
    highlight: no
    label_type: label
  delegate_to: localhost
  run_once: yes
'''

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'supported_by': 'community',
    'status': ['preview']
}


import atexit
import base64
import traceback

from io import BytesIO
from operator import itemgetter
from distutils.version import StrictVersion
from ansible.module_utils.basic import AnsibleModule, missing_required_lib

try:
    import pydotplus
    HAS_PYDOTPLUS = True
except ImportError:
    PYDOT_IMP_ERR = traceback.format_exc()
    HAS_PYDOTPLUS = False

try:
    import webcolors
    HAS_WEBCOLORS = True
except ImportError:
    WEBCOLORS_IMP_ERR = traceback.format_exc()
    HAS_WEBCOLORS = False

try:
    from zabbix_api import ZabbixAPI
    HAS_ZABBIX_API = True
except ImportError:
    ZBX_IMP_ERR = traceback.format_exc()
    HAS_ZABBIX_API = False

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    PIL_IMP_ERR = traceback.format_exc()
    HAS_PIL = False


class Map():
    def __init__(self, module, zbx):
        self._module = module
        self._zapi = zbx

        self.map_name = module.params['name']
        self.dot_data = module.params['data']
        self.width = module.params['width']
        self.height = module.params['height']
        self.state = module.params['state']
        self.default_image = module.params['default_image']
        self.map_id = self._get_sysmap_id(self.map_name)
        self.margin = module.params['margin']
        self.expand_problem = module.params['expand_problem']
        self.highlight = module.params['highlight']
        self.label_type = module.params['label_type']
        self.api_version = self._zapi.api_version()
        self.selements_sort_keys = self._get_selements_sort_keys()

    def _build_graph(self):
        try:
            graph_without_positions = pydotplus.graph_from_dot_data(self.dot_data)
            dot_data_with_positions = graph_without_positions.create_dot()
            graph_with_positions = pydotplus.graph_from_dot_data(dot_data_with_positions)
            if graph_with_positions:
                return graph_with_positions
        except Exception as e:
            self._module.fail_json(msg="Failed to build graph from DOT data: %s" % e)

    def get_map_config(self):
        if not self.dot_data:
            self._module.fail_json(msg="'data' is mandatory with state 'present'")
        graph = self._build_graph()
        nodes = self._get_graph_nodes(graph)
        edges = self._get_graph_edges(graph)
        icon_ids = self._get_icon_ids()
        map_config = {
            'name': self.map_name,
            'label_type': self._get_label_type_id(self.label_type),
            'expandproblem': int(self.expand_problem),
            'highlight': int(self.highlight),
            'width': self.width,
            'height': self.height,
            'selements': self._get_selements(graph, nodes, icon_ids),
            'links': self._get_links(nodes, edges),
        }
        return map_config

    def _get_label_type_id(self, label_type):
        label_type_ids = {
            'label': 0,
            'ip': 1,
            'name': 2,
            'status': 3,
            'nothing': 4,
            'custom': 5,
        }
        try:
            label_type_id = label_type_ids[label_type]
        except Exception as e:
            self._module.fail_json(msg="Failed to find id for label type '%s': %s" % (label_type, e))
        return label_type_id

    def _get_images_info(self, data, icon_ids):
        images = [
            {
                'dot_tag': 'zbx_image',
                'zbx_property': 'iconid_off',
                'mandatory': True
            },
            {
                'dot_tag': 'zbx_image_disabled',
                'zbx_property': 'iconid_disabled',
                'mandatory': False
            },
            {
                'dot_tag': 'zbx_image_maintenance',
                'zbx_property': 'iconid_maintenance',
                'mandatory': False
            },
            {
                'dot_tag': 'zbx_image_problem',
                'zbx_property': 'iconid_on',
                'mandatory': False
            }
        ]
        images_info = {}
        default_image = self.default_image if self.default_image else sorted(icon_ids.items())[0][0]
        for image in images:
            image_name = data.get(image['dot_tag'], None)
            if not image_name:
                if image['mandatory']:
                    image_name = default_image
                else:
                    continue
            image_name = remove_quotes(image_name)
            if image_name in icon_ids:
                images_info[image['zbx_property']] = icon_ids[image_name]
                if not image['mandatory']:
                    images_info['use_iconmap'] = 0
            else:
                self._module.fail_json(msg="Failed to find id for image '%s'" % image_name)
        return images_info

    def _get_element_type(self, data):
        types = {
            'host': 0,
            'sysmap': 1,
            'trigger': 2,
            'group': 3,
            'image': 4
        }
        element_type = {
            'elementtype': types['image'],
        }
        if StrictVersion(self.api_version) < StrictVersion('3.4'):
            element_type.update({
                'elementid': "0",
            })
        for type_name, type_id in sorted(types.items()):
            field_name = 'zbx_' + type_name
            if field_name in data:
                method_name = '_get_' + type_name + '_id'
                element_name = remove_quotes(data[field_name])
                get_element_id = getattr(self, method_name, None)
                if get_element_id:
                    elementid = get_element_id(element_name)
                    if elementid and int(elementid) > 0:
                        element_type.update({
                            'elementtype': type_id,
                            'label': element_name
                        })
                        if StrictVersion(self.api_version) < StrictVersion('3.4'):
                            element_type.update({
                                'elementid': elementid,
                            })
                        else:
                            element_type.update({
                                'elements': [{
                                    type_name + 'id': elementid,
                                }],
                            })
                        break
                    else:
                        self._module.fail_json(msg="Failed to find id for %s '%s'" % (type_name, element_name))
        return element_type

    # get list of map elements (nodes)
    def _get_selements(self, graph, nodes, icon_ids):
        selements = []
        icon_sizes = {}
        scales = self._get_scales(graph)
        for selementid, (node, data) in enumerate(nodes.items(), start=1):
            selement = {
                'selementid': selementid
            }
            data['selementid'] = selementid

            images_info = self._get_images_info(data, icon_ids)
            selement.update(images_info)
            image_id = images_info['iconid_off']
            if image_id not in icon_sizes:
                icon_sizes[image_id] = self._get_icon_size(image_id)

            pos = self._convert_coordinates(data['pos'], scales, icon_sizes[image_id])
            selement.update(pos)

            selement['label'] = remove_quotes(node)
            element_type = self._get_element_type(data)
            selement.update(element_type)

            label = self._get_label(data)
            if label:
                selement['label'] = label

            urls = self._get_urls(data)
            if urls:
                selement['urls'] = urls

            selements.append(selement)
        return selements

    def _get_links(self, nodes, edges):
        links = {}
        for edge in edges:
            link_id = tuple(sorted(edge.obj_dict['points']))
            node1, node2 = link_id
            data = edge.obj_dict['attributes']

            if "style" in data and data['style'] == "invis":
                continue

            if link_id not in links:
                links[link_id] = {
                    'selementid1': min(nodes[node1]['selementid'], nodes[node2]['selementid']),
                    'selementid2': max(nodes[node1]['selementid'], nodes[node2]['selementid']),
                }
            link = links[link_id]

            if "color" not in link:
                link['color'] = self._get_color_hex(remove_quotes(data.get('color', 'green')))

            if "zbx_draw_style" not in link:
                link['drawtype'] = self._get_link_draw_style_id(remove_quotes(data.get('zbx_draw_style', 'line')))

            label = self._get_label(data)
            if label and "label" not in link:
                link['label'] = label

            triggers = self._get_triggers(data)
            if triggers:
                if "linktriggers" not in link:
                    link['linktriggers'] = []
                link['linktriggers'] += triggers

        return list(links.values())

    def _get_urls(self, data):
        urls = []
        for url_raw in [remove_quotes(value) for key, value in data.items() if key.startswith("zbx_url")]:
            try:
                name, url = url_raw.split(':', 1)
            except Exception as e:
                self._module.fail_json(msg="Failed to parse zbx_url='%s': %s" % (url_raw, e))
            urls.append({
                'name': name,
                'url': url,
            })
        return urls

    def _get_triggers(self, data):
        triggers = []
        for trigger_definition in [remove_quotes(value) for key, value in data.items() if key.startswith("zbx_trigger")]:
            triggerid = self._get_trigger_id(trigger_definition)
            if triggerid:
                triggers.append({
                    'triggerid': triggerid,
                    'color': self._get_color_hex(remove_quotes(data.get('zbx_trigger_color', 'red'))),
                    'drawtype': self._get_link_draw_style_id(remove_quotes(data.get('zbx_trigger_draw_style', 'bold'))),
                })
            else:
                self._module.fail_json(msg="Failed to find trigger '%s'" % (trigger_definition))
        return triggers

    @staticmethod
    def _get_label(data, default=None):
        if "zbx_label" in data:
            label = remove_quotes(data['zbx_label']).replace('\\n', '\n')
        elif "label" in data:
            label = remove_quotes(data['label'])
        else:
            label = default
        return label

    def _get_sysmap_id(self, map_name):
        exist_map = self._zapi.map.get({'filter': {'name': map_name}})
        if exist_map:
            return exist_map[0]['sysmapid']
        return None

    def _get_group_id(self, group_name):
        exist_group = self._zapi.hostgroup.get({'filter': {'name': group_name}})
        if exist_group:
            return exist_group[0]['groupid']
        return None

    def map_exists(self):
        return bool(self.map_id)

    def create_map(self, map_config):
        try:
            if self._module.check_mode:
                self._module.exit_json(changed=True)
            result = self._zapi.map.create(map_config)
            if result:
                return result
        except Exception as e:
            self._module.fail_json(msg="Failed to create map: %s" % e)

    def update_map(self, map_config):
        if not self.map_id:
            self._module.fail_json(msg="Failed to update map: map_id is unknown. Try to create_map instead.")
        try:
            if self._module.check_mode:
                self._module.exit_json(changed=True)
            map_config['sysmapid'] = self.map_id
            result = self._zapi.map.update(map_config)
            if result:
                return result
        except Exception as e:
            self._module.fail_json(msg="Failed to update map: %s" % e)

    def delete_map(self):
        if not self.map_id:
            self._module.fail_json(msg="Failed to delete map: map_id is unknown.")
        try:
            if self._module.check_mode:
                self._module.exit_json(changed=True)
            self._zapi.map.delete([self.map_id])
        except Exception as e:
            self._module.fail_json(msg="Failed to delete map, Exception: %s" % e)

    def is_exist_map_correct(self, generated_map_config):
        exist_map_configs = self._zapi.map.get({
            'sysmapids': self.map_id,
            'selectLinks': 'extend',
            'selectSelements': 'extend'
        })
        exist_map_config = exist_map_configs[0]
        if not self._is_dicts_equal(generated_map_config, exist_map_config):
            return False
        if not self._is_selements_equal(generated_map_config['selements'], exist_map_config['selements']):
            return False
        self._update_ids(generated_map_config, exist_map_config)
        if not self._is_links_equal(generated_map_config['links'], exist_map_config['links']):
            return False
        return True

    def _get_selements_sort_keys(self):
        keys_to_sort = ['label']
        if StrictVersion(self.api_version) < StrictVersion('3.4'):
            keys_to_sort.insert(0, 'elementid')
        return keys_to_sort

    def _is_selements_equal(self, generated_selements, exist_selements):
        if len(generated_selements) != len(exist_selements):
            return False
        generated_selements_sorted = sorted(generated_selements, key=itemgetter(*self.selements_sort_keys))
        exist_selements_sorted = sorted(exist_selements, key=itemgetter(*self.selements_sort_keys))
        for (generated_selement, exist_selement) in zip(generated_selements_sorted, exist_selements_sorted):
            if StrictVersion(self.api_version) >= StrictVersion("3.4"):
                if not self._is_elements_equal(generated_selement.get('elements', []), exist_selement.get('elements', [])):
                    return False
            if not self._is_dicts_equal(generated_selement, exist_selement, ['selementid']):
                return False
            if not self._is_urls_equal(generated_selement.get('urls', []), exist_selement.get('urls', [])):
                return False
        return True

    def _is_urls_equal(self, generated_urls, exist_urls):
        if len(generated_urls) != len(exist_urls):
            return False
        generated_urls_sorted = sorted(generated_urls, key=itemgetter('name', 'url'))
        exist_urls_sorted = sorted(exist_urls, key=itemgetter('name', 'url'))
        for (generated_url, exist_url) in zip(generated_urls_sorted, exist_urls_sorted):
            if not self._is_dicts_equal(generated_url, exist_url, ['selementid']):
                return False
        return True

    def _is_elements_equal(self, generated_elements, exist_elements):
        if len(generated_elements) != len(exist_elements):
            return False
        generated_elements_sorted = sorted(generated_elements, key=lambda k: k.values()[0])
        exist_elements_sorted = sorted(exist_elements, key=lambda k: k.values()[0])
        for (generated_element, exist_element) in zip(generated_elements_sorted, exist_elements_sorted):
            if not self._is_dicts_equal(generated_element, exist_element, ['selementid']):
                return False
        return True

    # since generated IDs differ from real Zabbix ones, make real IDs match generated ones
    def _update_ids(self, generated_map_config, exist_map_config):
        generated_selements_sorted = sorted(generated_map_config['selements'], key=itemgetter(*self.selements_sort_keys))
        exist_selements_sorted = sorted(exist_map_config['selements'], key=itemgetter(*self.selements_sort_keys))
        id_mapping = {}
        for (generated_selement, exist_selement) in zip(generated_selements_sorted, exist_selements_sorted):
            id_mapping[exist_selement['selementid']] = generated_selement['selementid']
        for link in exist_map_config['links']:
            link['selementid1'] = id_mapping[link['selementid1']]
            link['selementid2'] = id_mapping[link['selementid2']]
            if link['selementid2'] < link['selementid1']:
                link['selementid1'], link['selementid2'] = link['selementid2'], link['selementid1']

    def _is_links_equal(self, generated_links, exist_links):
        if len(generated_links) != len(exist_links):
            return False
        generated_links_sorted = sorted(generated_links, key=itemgetter('selementid1', 'selementid2', 'color', 'drawtype'))
        exist_links_sorted = sorted(exist_links, key=itemgetter('selementid1', 'selementid2', 'color', 'drawtype'))
        for (generated_link, exist_link) in zip(generated_links_sorted, exist_links_sorted):
            if not self._is_dicts_equal(generated_link, exist_link, ['selementid1', 'selementid2']):
                return False
            if not self._is_triggers_equal(generated_link.get('linktriggers', []), exist_link.get('linktriggers', [])):
                return False
        return True

    def _is_triggers_equal(self, generated_triggers, exist_triggers):
        if len(generated_triggers) != len(exist_triggers):
            return False
        generated_triggers_sorted = sorted(generated_triggers, key=itemgetter('triggerid'))
        exist_triggers_sorted = sorted(exist_triggers, key=itemgetter('triggerid'))
        for (generated_trigger, exist_trigger) in zip(generated_triggers_sorted, exist_triggers_sorted):
            if not self._is_dicts_equal(generated_trigger, exist_trigger):
                return False
        return True

    @staticmethod
    def _is_dicts_equal(d1, d2, exclude_keys=None):
        if exclude_keys is None:
            exclude_keys = []
        for key in d1.keys():
            if isinstance(d1[key], dict) or isinstance(d1[key], list):
                continue
            if key in exclude_keys:
                continue
            # compare as strings since Zabbix API returns everything as strings
            if key not in d2 or str(d2[key]) != str(d1[key]):
                return False
        return True

    def _get_host_id(self, hostname):
        hostid = self._zapi.host.get({'filter': {'host': hostname}})
        if hostid:
            return str(hostid[0]['hostid'])

    def _get_trigger_id(self, trigger_definition):
        try:
            host, trigger = trigger_definition.split(':', 1)
        except Exception as e:
            self._module.fail_json(msg="Failed to parse zbx_trigger='%s': %s" % (trigger_definition, e))
        triggerid = self._zapi.trigger.get({
            'host': host,
            'filter': {
                'description': trigger
            }
        })
        if triggerid:
            return str(triggerid[0]['triggerid'])

    def _get_icon_ids(self):
        icons_list = self._zapi.image.get({})
        icon_ids = {}
        for icon in icons_list:
            icon_ids[icon['name']] = icon['imageid']
        return icon_ids

    def _get_icon_size(self, icon_id):
        icons_list = self._zapi.image.get({
            'imageids': [
                icon_id
            ],
            'select_image': True
        })
        if len(icons_list) > 0:
            icon_base64 = icons_list[0]['image']
        else:
            self._module.fail_json(msg="Failed to find image with id %s" % icon_id)
        image = Image.open(BytesIO(base64.b64decode(icon_base64)))
        icon_width, icon_height = image.size
        return icon_width, icon_height

    @staticmethod
    def _get_node_attributes(node):
        attr = {}
        if "attributes" in node.obj_dict:
            attr.update(node.obj_dict['attributes'])
        pos = node.get_pos()
        if pos is not None:
            pos = remove_quotes(pos)
            xx, yy = pos.split(",")
            attr['pos'] = (float(xx), float(yy))
        return attr

    def _get_graph_nodes(self, parent):
        nodes = {}
        for node in parent.get_nodes():
            node_name = node.get_name()
            if node_name in ('node', 'graph', 'edge'):
                continue
            nodes[node_name] = self._get_node_attributes(node)
        for subgraph in parent.get_subgraphs():
            nodes.update(self._get_graph_nodes(subgraph))
        return nodes

    def _get_graph_edges(self, parent):
        edges = []
        for edge in parent.get_edges():
            edges.append(edge)
        for subgraph in parent.get_subgraphs():
            edges += self._get_graph_edges(subgraph)
        return edges

    def _get_scales(self, graph):
        bb = remove_quotes(graph.get_bb())
        min_x, min_y, max_x, max_y = bb.split(",")
        scale_x = (self.width - self.margin * 2) / (float(max_x) - float(min_x)) if float(max_x) != float(min_x) else 0
        scale_y = (self.height - self.margin * 2) / (float(max_y) - float(min_y)) if float(max_y) != float(min_y) else 0
        return {
            'min_x': float(min_x),
            'min_y': float(min_y),
            'max_x': float(max_x),
            'max_y': float(max_y),
            'scale_x': float(scale_x),
            'scale_y': float(scale_y),
        }

    # transform Graphviz coordinates to Zabbix's ones
    def _convert_coordinates(self, pos, scales, icon_size):
        return {
            'x': int((pos[0] - scales['min_x']) * scales['scale_x'] - icon_size[0] / 2 + self.margin),
            'y': int((scales['max_y'] - pos[1] + scales['min_y']) * scales['scale_y'] - icon_size[1] / 2 + self.margin),
        }

    def _get_color_hex(self, color_name):
        if color_name.startswith('#'):
            color_hex = color_name
        else:
            try:
                color_hex = webcolors.name_to_hex(color_name)
            except Exception as e:
                self._module.fail_json(msg="Failed to get RGB hex for color '%s': %s" % (color_name, e))
        color_hex = color_hex.strip('#').upper()
        return color_hex

    def _get_link_draw_style_id(self, draw_style):
        draw_style_ids = {
            'line': 0,
            'bold': 2,
            'dotted': 3,
            'dashed': 4
        }
        try:
            draw_style_id = draw_style_ids[draw_style]
        except Exception as e:
            self._module.fail_json(msg="Failed to find id for draw type '%s': %s" % (draw_style, e))
        return draw_style_id


# If a string has single or double quotes around it, remove them.
def remove_quotes(s):
    if (s[0] == s[-1]) and s.startswith(("'", '"')):
        s = s[1:-1]
    return s


def main():
    module = AnsibleModule(
        argument_spec=dict(
            server_url=dict(type='str', required=True, aliases=['url']),
            login_user=dict(type='str', required=True),
            login_password=dict(type='str', required=True, no_log=True),
            http_login_user=dict(type='str', required=False, default=None),
            http_login_password=dict(type='str', required=False, default=None, no_log=True),
            timeout=dict(type='int', default=10),
            validate_certs=dict(type='bool', required=False, default=True),
            name=dict(type='str', required=True, aliases=['map_name']),
            data=dict(type='str', required=False, aliases=['dot_data']),
            width=dict(type='int', default=800),
            height=dict(type='int', default=600),
            state=dict(type='str', default="present", choices=['present', 'absent']),
            default_image=dict(type='str', required=False, aliases=['image']),
            margin=dict(type='int', default=40),
            expand_problem=dict(type='bool', default=True),
            highlight=dict(type='bool', default=True),
            label_type=dict(type='str', default='name', choices=['label', 'ip', 'name', 'status', 'nothing', 'custom']),
        ),
        supports_check_mode=True
    )

    if not HAS_ZABBIX_API:
        module.fail_json(msg=missing_required_lib('zabbix-api', url='https://pypi.org/project/zabbix-api/'), exception=ZBX_IMP_ERR)
    if not HAS_PYDOTPLUS:
        module.fail_json(msg=missing_required_lib('pydotplus', url='https://pypi.org/project/pydotplus/'), exception=PYDOT_IMP_ERR)
    if not HAS_WEBCOLORS:
        module.fail_json(msg=missing_required_lib('webcolors', url='https://pypi.org/project/webcolors/'), exception=WEBCOLORS_IMP_ERR)
    if not HAS_PIL:
        module.fail_json(msg=missing_required_lib('Pillow', url='https://pypi.org/project/Pillow/'), exception=PIL_IMP_ERR)

    server_url = module.params['server_url']
    login_user = module.params['login_user']
    login_password = module.params['login_password']
    http_login_user = module.params['http_login_user']
    http_login_password = module.params['http_login_password']
    timeout = module.params['timeout']
    validate_certs = module.params['validate_certs']

    zbx = None

    # login to zabbix
    try:
        zbx = ZabbixAPI(server_url, timeout=timeout, user=http_login_user, passwd=http_login_password,
                        validate_certs=validate_certs)
        zbx.login(login_user, login_password)
        atexit.register(zbx.logout)
    except Exception as e:
        module.fail_json(msg="Failed to connect to Zabbix server: %s" % e)

    sysmap = Map(module, zbx)

    if sysmap.state == "absent":
        if sysmap.map_exists():
            sysmap.delete_map()
            module.exit_json(changed=True, result="Successfully deleted map: %s" % sysmap.map_name)
        else:
            module.exit_json(changed=False)
    else:
        map_config = sysmap.get_map_config()
        if sysmap.map_exists():
            if sysmap.is_exist_map_correct(map_config):
                module.exit_json(changed=False)
            else:
                sysmap.update_map(map_config)
                module.exit_json(changed=True, result="Successfully updated map: %s" % sysmap.map_name)
        else:
            sysmap.create_map(map_config)
            module.exit_json(changed=True, result="Successfully created map: %s" % sysmap.map_name)


if __name__ == '__main__':
    main()
