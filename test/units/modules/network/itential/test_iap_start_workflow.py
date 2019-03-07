"""
iap_token unit tests
"""
# -*- coding: utf-8 -*-

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

# pylint: disable=invalid-name,protected-access,function-redefined,unused-argument
# pylint: disable=unused-import,redundant-unittest-assert

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

import mock
import unittest
from ansible.modules.network.itential import iap_start_workflow


class TestWorkflowModule(unittest.TestCase):

    @mock.patch('ansible.modules.network.itential.iap_start_workflow.start_workflow')
    def test_iap_workflow(self, iap_workflow):
        params = {"description": "NewTestAnsible",
                  "https": "false",
                  "iap_fqdn": "localhost",
                  "iap_port": "3000",
                  "token_key": "NDM2OGJlMzg5MjRlMTQyNzc0YmZmNmQ5ZWRkYzcyYTE=",
                  "validate_certs": "false",
                  "variables": {
                      "value": "3333"
                  },
                  "workflow_name": "DummyWF"}

        module = {"params": params}
        return_response = {
            "_id": "e17646fc7a8f4a6a9e691fe4",
            "created": "2018-09-15T21:57:50.388Z",
            "created_by": "5b8fe4fcb3f8b800134ea5fd",
            "description": "NewTestAnsible",
            "font_size": 12,
            "groups": [],
            "last_updated": "2019-02-22T15:55:40.197Z",
            "last_updated_by": "5b8fe4fcb3f8b800134ea5fd",
            "locked": 'false',
            "metrics": {
                "progress": 0,
                "start_time": 1551043499742,
                "user": "5b8fe4fcb3f8b800134ea5fd"
            },
            "name": "DummyWF",
            "status": "running",
            "tasks": {
                "10d1": {
                    "_id": "1ca495e4-dc86-41df-b3ca-8c215920ec91",
                    "app": "WorkFlowEngine",
                    "deprecated": 'false',
                    "description": "Create a new Job variable by Job ID and assign it a value.",
                    "displayName": "WorkFlowEngine",
                    "groups": [],
                    "iterations": [
                        "1ca495e4-dc86-41df-b3ca-8c215920ec91"
                    ],
                    "job": {
                        "_id": "e17646fc7a8f4a6a9e691fe4",
                        "description": "NewTestAnsible",
                        "index": 0,
                        "name": "DummyWF",
                        "task": "10d1"
                    },
                    "location": "Application",
                    "locked": 'false',
                    "matched": [
                        {
                            "highlightString": "<span class='highlight-string'>new</span>Variable",
                            "key": "name"
                        },
                        {
                            "highlightString": "Create a <span class='highlight-string'>new</span> "
                                               "Job variable by Job ID and assign it a value.",
                            "key": "description"
                        }
                    ],
                    "metrics": {
                        "owner": ""
                    },
                    "name": "newVariable",
                    "status": "incomplete",
                    "summary": "Create a Job Variable",
                    "type": "operation",
                    "variables": {
                        "incoming": {
                            "name": "anyVar",
                            "value": {
                                "hello": "hello_from_the_other"
                            }
                        },
                        "outgoing": {
                            "value": 'null'
                        }
                    },
                    "x": 0.24,
                    "y": 0.3904899135446686
                },
                "50c1": {
                    "_id": "33a32349-c151-4b67-b1cb-d5df2147772f",
                    "actor": "Pronghorn",
                    "app": "StringMethods",
                    "deprecated": 'false',
                    "description": "Concatenates a string with a second string(s). The second parameter can be a "
                                   "string or array.",
                    "displayName": "String",
                    "groups": [],
                    "iterations": [
                        "33a32349-c151-4b67-b1cb-d5df2147772f"
                    ],
                    "job": {
                        "_id": "e17646fc7a8f4a6a9e691fe4",
                        "description": "NewTestAnsible",
                        "index": 0,
                        "name": "DummyWF",
                        "task": "50c1"
                    },
                    "location": "Application",
                    "locked": 'false',
                    "matched": [
                        {
                            "highlightString": "<span class='highlight-string'>Strin</span>gMethods",
                            "key": "app"
                        },
                        {
                            "highlightString": "Concatenates <span class='highlight-string'>"
                                               "strin</span>gs together.",
                            "key": "summary"
                        },
                        {
                            "highlightString": "Concatenates a <span class='highlight-string'>strin</span>g "
                                               "with a second string(s). The second parameter "
                                               "can be a string or array.",
                            "key": "description"
                        }
                    ],
                    "metrics": {
                        "owner": ""
                    },
                    "name": "concat",
                    "scheduled": 'false',
                    "status": "incomplete",
                    "summary": "Concatenates strings together.",
                    "type": "automatic",
                    "variables": {
                        "error": "",
                        "incoming": {
                            "str": "$var.5023.return_data",
                            "stringN": [
                                "_side"
                            ]
                        },
                        "outgoing": {
                            "combinedStrings": 'null'
                        }
                    },
                    "x": 0.37,
                    "y": 0.17002881844380405
                },
                "5023": {
                    "_id": "56396de1-c7b5-495e-aff8-342fe168a2b1",
                    "app": "WorkFlowEngine",
                    "deprecated": 'false',
                    "description": "Query data using a dot/bracket notation string and a matching key/value pair.",
                    "displayName": "WorkFlowEngine",
                    "groups": [],
                    "iterations": [
                        "56396de1-c7b5-495e-aff8-342fe168a2b1"
                    ],
                    "job": {
                        "_id": "e17646fc7a8f4a6a9e691fe4",
                        "description": "NewTestAnsible",
                        "index": 0,
                        "name": "DummyWF",
                        "task": "5023"
                    },
                    "location": "Application",
                    "locked": 'false',
                    "matched": [
                        {
                            "highlightString": "<span class='highlight-string'>query</span>",
                            "key": "name"
                        },
                        {
                            "highlightString": "<span class='highlight-string'>Query</span> Data Using "
                                               "'json-query' Format",
                            "key": "summary"
                        },
                        {
                            "highlightString": "<span class='highlight-string'>Query</span> data using a "
                                               "dot/bracket notation string and a matching key/value pair.",
                            "key": "description"
                        }
                    ],
                    "metrics": {
                        "owner": ""
                    },
                    "name": "query",
                    "scheduled": 'false',
                    "status": "incomplete",
                    "summary": "Query Data Using 'json-query' Format",
                    "type": "operation",
                    "variables": {
                        "error": "",
                        "incoming": {
                            "obj": "$var.10d1.value",
                            "pass_on_'null'": 'false',
                            "query": "hello"
                        },
                        "outgoing": {
                            "return_data": 'null'
                        }
                    },
                    "x": 0.2630769230769231,
                    "y": 0.2420749279538905
                },
                "7cd4": {
                    "_id": "dc132a1a-4ac8-4bfe-b75d-ea95eac84d09",
                    "actor": "job",
                    "app": "WorkFlowEngine",
                    "deprecated": 'false',
                    "description": "Run a child Job inside a Workflow",
                    "displayName": "WorkFlowEngine",
                    "groups": [],
                    "iterations": [
                        "dc132a1a-4ac8-4bfe-b75d-ea95eac84d09"
                    ],
                    "job": {
                        "_id": "e17646fc7a8f4a6a9e691fe4",
                        "description": "NewTestAnsible",
                        "index": 0,
                        "name": "DummyWF",
                        "task": "7cd4"
                    },
                    "location": "Application",
                    "locked": 'false',
                    "matched": [
                        {
                            "highlightString": "<span class='highlight-string'>child</span>Job",
                            "key": "name"
                        },
                        {
                            "highlightString": "Run <span class='highlight-string'>Child</span> Job",
                            "key": "summary"
                        },
                        {
                            "highlightString": "Run a <span class='highlight-string'>child</span>"
                                               " Job inside a Workflow",
                            "key": "description"
                        }
                    ],
                    "metrics": {
                        "owner": ""
                    },
                    "name": "childJob",
                    "status": "incomplete",
                    "summary": "Run Child Job",
                    "type": "operation",
                    "variables": {
                        "incoming": {
                            "task": "",
                            "variables": {
                                "child1_body": {
                                    "task": "50c1",
                                    "value": "combinedStrings",
                                    "variable": ""
                                }
                            },
                            "workflow": "child1"
                        },
                        "outgoing": {
                            "job_details": 'null'
                        }
                    },
                    "x": 0.6146153846153846,
                    "y": 0.40634005763688763
                },
                "87f4": {
                    "_id": "1f5da682-b377-4739-a60d-31d897c59863",
                    "app": "MOP",
                    "deprecated": 'false',
                    "description": "MOP confirm Task",
                    "displayName": "MOP",
                    "groups": [
                        "5b8fe4fcb3f8b800134ea5fc"
                    ],
                    "iterations": [
                        "1f5da682-b377-4739-a60d-31d897c59863"
                    ],
                    "job": {
                        "_id": "e17646fc7a8f4a6a9e691fe4",
                        "description": "NewTestAnsible",
                        "index": 0,
                        "name": "DummyWF",
                        "task": "87f4"
                    },
                    "location": "Application",
                    "locked": 'false',
                    "matched": [
                        {
                            "highlightString": "<span class='highlight-string'>confirm</span>Task",
                            "key": "name"
                        },
                        {
                            "highlightString": "MOP <span class='highlight-string'>confirm</span> Task",
                            "key": "summary"
                        },
                        {
                            "highlightString": "MOP <span class='highlight-string'>confirm</span> Task",
                            "key": "description"
                        }
                    ],
                    "metrics": {
                        "owner": ""
                    },
                    "name": "confirmTask",
                    "scheduled": 'false',
                    "status": "incomplete",
                    "summary": "MOP confirm Task",
                    "type": "manual",
                    "variables": {
                        "error": "",
                        "incoming": {
                            "body": "<!value_output!>",
                            "title": "Run Time Var",
                            "variables": "$var.f97e.value"
                        },
                        "outgoing": {}
                    },
                    "view": "/mop/task/confirmTask",
                    "x": 0.6961538461538461,
                    "y": 0.06772334293948126
                },
                "f97e": {
                    "_id": "38017b10-5e26-4161-bccb-c2f983dcf1ca",
                    "app": "WorkFlowEngine",
                    "deprecated": 'false',
                    "description": "Create a new Job variable by Job ID and assign it a value.",
                    "displayName": "WorkFlowEngine",
                    "groups": [],
                    "iterations": [
                        "38017b10-5e26-4161-bccb-c2f983dcf1ca"
                    ],
                    "job": {
                        "_id": "e17646fc7a8f4a6a9e691fe4",
                        "description": "NewTestAnsible",
                        "index": 0,
                        "name": "DummyWF",
                        "task": "f97e"
                    },
                    "location": "Application",
                    "locked": 'false',
                    "matched": [
                        {
                            "highlightString": "<span class='highlight-string'>new</span>Variable",
                            "key": "name"
                        },
                        {
                            "highlightString": "Create a <span class='highlight-string'>new</span>"
                                               " Job variable by Job ID and assign it a value.",
                            "key": "description"
                        }
                    ],
                    "metrics": {
                        "owner": ""
                    },
                    "name": "newVariable",
                    "status": "incomplete",
                    "summary": "Create a Job Variable",
                    "type": "operation",
                    "variables": {
                        "incoming": {
                            "name": "run_time",
                            "value": {
                                "value_output": "I am RunTime Variable"
                            }
                        },
                        "outgoing": {
                            "value": 'null'
                        }
                    },
                    "x": 0.45615384615384613,
                    "y": -0.04755043227665706
                },
                "workflow_end": {
                    "groups": [],
                    "name": "workflow_end",
                    "status": "incomplete",
                    "x": 0.9,
                    "y": 0.5979827089337176
                },
                "workflow_start": {
                    "groups": [],
                    "metrics": {
                        "finish_state": "success",
                        "start_time": 1551043499742,
                        "user": "5b8fe4fcb3f8b800134ea5fd"
                    },
                    "name": "workflow_start",
                    "status": "complete",
                    "x": 0.04692307692307692,
                    "y": 0.6023054755043228
                }
            },
            "transitions": {
                "10d1": {
                    "5023": {
                        "state": "success",
                        "type": "standard"
                    }
                },
                "5023": {
                    "50c1": {
                        "state": "success",
                        "type": "standard"
                    }
                },
                "50c1": {
                    "f97e": {
                        "state": "success",
                        "type": "standard"
                    }
                },
                "7cd4": {
                    "workflow_end": {
                        "state": "success",
                        "type": "standard"
                    }
                },
                "87f4": {
                    "7cd4": {
                        "state": "success",
                        "type": "standard"
                    }
                },
                "f97e": {
                    "87f4": {
                        "state": "success",
                        "type": "standard"
                    }
                },
                "workflow_end": {},
                "workflow_start": {
                    "10d1": {
                        "state": "success",
                        "type": "standard"
                    }
                }
            },
            "type": "automation",
            "variables": {
                "_id": "e17646fc7a8f4a6a9e691fe4",
                "initiator": "admin@pronghorn",
                "value": "3333"
            },
            "watchers": [
                "5b8fe4fcb3f8b800134ea5fd"
            ]
        }
        iap_workflow.return_value = {
            "_id": "e17646fc7a8f4a6a9e691fe4",
            "created": "2018-09-15T21:57:50.388Z",
            "created_by": "5b8fe4fcb3f8b800134ea5fd",
            "description": "NewTestAnsible",
            "font_size": 12,
            "groups": [],
            "last_updated": "2019-02-22T15:55:40.197Z",
            "last_updated_by": "5b8fe4fcb3f8b800134ea5fd",
            "locked": 'false',
            "metrics": {
                "progress": 0,
                "start_time": 1551043499742,
                "user": "5b8fe4fcb3f8b800134ea5fd"
            },
            "name": "DummyWF",
            "status": "running",
            "tasks": {
                "10d1": {
                    "_id": "1ca495e4-dc86-41df-b3ca-8c215920ec91",
                    "app": "WorkFlowEngine",
                    "deprecated": 'false',
                    "description": "Create a new Job variable by Job ID and assign it a value.",
                    "displayName": "WorkFlowEngine",
                    "groups": [],
                    "iterations": [
                        "1ca495e4-dc86-41df-b3ca-8c215920ec91"
                    ],
                    "job": {
                        "_id": "e17646fc7a8f4a6a9e691fe4",
                        "description": "NewTestAnsible",
                        "index": 0,
                        "name": "DummyWF",
                        "task": "10d1"
                    },
                    "location": "Application",
                    "locked": 'false',
                    "matched": [
                        {
                            "highlightString": "<span class='highlight-string'>new</span>Variable",
                            "key": "name"
                        },
                        {
                            "highlightString": "Create a <span class='highlight-string'>new</span> "
                                               "Job variable by Job ID and assign it a value.",
                            "key": "description"
                        }
                    ],
                    "metrics": {
                        "owner": ""
                    },
                    "name": "newVariable",
                    "status": "incomplete",
                    "summary": "Create a Job Variable",
                    "type": "operation",
                    "variables": {
                        "incoming": {
                            "name": "anyVar",
                            "value": {
                                "hello": "hello_from_the_other"
                            }
                        },
                        "outgoing": {
                            "value": 'null'
                        }
                    },
                    "x": 0.24,
                    "y": 0.3904899135446686
                },
                "5023": {
                    "_id": "56396de1-c7b5-495e-aff8-342fe168a2b1",
                    "app": "WorkFlowEngine",
                    "deprecated": 'false',
                    "description": "Query data using a dot/bracket notation string and a matching key/value pair.",
                    "displayName": "WorkFlowEngine",
                    "groups": [],
                    "iterations": [
                        "56396de1-c7b5-495e-aff8-342fe168a2b1"
                    ],
                    "job": {
                        "_id": "e17646fc7a8f4a6a9e691fe4",
                        "description": "NewTestAnsible",
                        "index": 0,
                        "name": "DummyWF",
                        "task": "5023"
                    },
                    "location": "Application",
                    "locked": 'false',
                    "matched": [
                        {
                            "highlightString": "<span class='highlight-string'>query</span>",
                            "key": "name"
                        },
                        {
                            "highlightString": "<span class='highlight-string'>Query</span> "
                                               "Data Using 'json-query' Format",
                            "key": "summary"
                        },
                        {
                            "highlightString": "<span class='highlight-string'>Query</span> "
                                               "data using a dot/bracket notation string and a "
                                               "matching key/value pair.",
                            "key": "description"
                        }
                    ],
                    "metrics": {
                        "owner": ""
                    },
                    "name": "query",
                    "scheduled": 'false',
                    "status": "incomplete",
                    "summary": "Query Data Using 'json-query' Format",
                    "type": "operation",
                    "variables": {
                        "error": "",
                        "incoming": {
                            "obj": "$var.10d1.value",
                            "pass_on_'null'": 'false',
                            "query": "hello"
                        },
                        "outgoing": {
                            "return_data": 'null'
                        }
                    },
                    "x": 0.2630769230769231,
                    "y": 0.2420749279538905
                },
                "50c1": {
                    "_id": "33a32349-c151-4b67-b1cb-d5df2147772f",
                    "actor": "Pronghorn",
                    "app": "StringMethods",
                    "deprecated": 'false',
                    "description": "Concatenates a string with a second string(s). "
                                   "The second parameter can be a string or array.",
                    "displayName": "String",
                    "groups": [],
                    "iterations": [
                        "33a32349-c151-4b67-b1cb-d5df2147772f"
                    ],
                    "job": {
                        "_id": "e17646fc7a8f4a6a9e691fe4",
                        "description": "NewTestAnsible",
                        "index": 0,
                        "name": "DummyWF",
                        "task": "50c1"
                    },
                    "location": "Application",
                    "locked": 'false',
                    "matched": [
                        {
                            "highlightString": "<span class='highlight-string'>Strin</span>gMethods",
                            "key": "app"
                        },
                        {
                            "highlightString": "Concatenates <span class='highlight-string'>strin</span>gs together.",
                            "key": "summary"
                        },
                        {
                            "highlightString": "Concatenates a <span class='highlight-string'>strin</span>g "
                                               "with a second string(s). The second parameter "
                                               "can be a string or array.",
                            "key": "description"
                        }
                    ],
                    "metrics": {
                        "owner": ""
                    },
                    "name": "concat",
                    "scheduled": 'false',
                    "status": "incomplete",
                    "summary": "Concatenates strings together.",
                    "type": "automatic",
                    "variables": {
                        "error": "",
                        "incoming": {
                            "str": "$var.5023.return_data",
                            "stringN": [
                                "_side"
                            ]
                        },
                        "outgoing": {
                            "combinedStrings": 'null'
                        }
                    },
                    "x": 0.37,
                    "y": 0.17002881844380405
                },
                "7cd4": {
                    "_id": "dc132a1a-4ac8-4bfe-b75d-ea95eac84d09",
                    "actor": "job",
                    "app": "WorkFlowEngine",
                    "deprecated": 'false',
                    "description": "Run a child Job inside a Workflow",
                    "displayName": "WorkFlowEngine",
                    "groups": [],
                    "iterations": [
                        "dc132a1a-4ac8-4bfe-b75d-ea95eac84d09"
                    ],
                    "job": {
                        "_id": "e17646fc7a8f4a6a9e691fe4",
                        "description": "NewTestAnsible",
                        "index": 0,
                        "name": "DummyWF",
                        "task": "7cd4"
                    },
                    "location": "Application",
                    "locked": 'false',
                    "matched": [
                        {
                            "highlightString": "<span class='highlight-string'>child</span>Job",
                            "key": "name"
                        },
                        {
                            "highlightString": "Run <span class='highlight-string'>Child</span> Job",
                            "key": "summary"
                        },
                        {
                            "highlightString": "Run a <span class='highlight-string'>child</span> "
                                               "Job inside a Workflow",
                            "key": "description"
                        }
                    ],
                    "metrics": {
                        "owner": ""
                    },
                    "name": "childJob",
                    "status": "incomplete",
                    "summary": "Run Child Job",
                    "type": "operation",
                    "variables": {
                        "incoming": {
                            "task": "",
                            "variables": {
                                "child1_body": {
                                    "task": "50c1",
                                    "value": "combinedStrings",
                                    "variable": ""
                                }
                            },
                            "workflow": "child1"
                        },
                        "outgoing": {
                            "job_details": 'null'
                        }
                    },
                    "x": 0.6146153846153846,
                    "y": 0.40634005763688763
                },
                "87f4": {
                    "_id": "1f5da682-b377-4739-a60d-31d897c59863",
                    "app": "MOP",
                    "deprecated": 'false',
                    "description": "MOP confirm Task",
                    "displayName": "MOP",
                    "groups": [
                        "5b8fe4fcb3f8b800134ea5fc"
                    ],
                    "iterations": [
                        "1f5da682-b377-4739-a60d-31d897c59863"
                    ],
                    "job": {
                        "_id": "e17646fc7a8f4a6a9e691fe4",
                        "description": "NewTestAnsible",
                        "index": 0,
                        "name": "DummyWF",
                        "task": "87f4"
                    },
                    "location": "Application",
                    "locked": 'false',
                    "matched": [
                        {
                            "highlightString": "<span class='highlight-string'>confirm</span>Task",
                            "key": "name"
                        },
                        {
                            "highlightString": "MOP <span class='highlight-string'>confirm</span> Task",
                            "key": "summary"
                        },
                        {
                            "highlightString": "MOP <span class='highlight-string'>confirm</span> Task",
                            "key": "description"
                        }
                    ],
                    "metrics": {
                        "owner": ""
                    },
                    "name": "confirmTask",
                    "scheduled": 'false',
                    "status": "incomplete",
                    "summary": "MOP confirm Task",
                    "type": "manual",
                    "variables": {
                        "error": "",
                        "incoming": {
                            "body": "<!value_output!>",
                            "title": "Run Time Var",
                            "variables": "$var.f97e.value"
                        },
                        "outgoing": {}
                    },
                    "view": "/mop/task/confirmTask",
                    "x": 0.6961538461538461,
                    "y": 0.06772334293948126
                },
                "f97e": {
                    "_id": "38017b10-5e26-4161-bccb-c2f983dcf1ca",
                    "app": "WorkFlowEngine",
                    "deprecated": 'false',
                    "description": "Create a new Job variable by Job ID and assign it a value.",
                    "displayName": "WorkFlowEngine",
                    "groups": [],
                    "iterations": [
                        "38017b10-5e26-4161-bccb-c2f983dcf1ca"
                    ],
                    "job": {
                        "_id": "e17646fc7a8f4a6a9e691fe4",
                        "description": "NewTestAnsible",
                        "index": 0,
                        "name": "DummyWF",
                        "task": "f97e"
                    },
                    "location": "Application",
                    "locked": 'false',
                    "matched": [
                        {
                            "highlightString": "<span class='highlight-string'>new</span>Variable",
                            "key": "name"
                        },
                        {
                            "highlightString": "Create a <span class='highlight-string'>new</span> "
                                               "Job variable by Job ID and assign it a value.",
                            "key": "description"
                        }
                    ],
                    "metrics": {
                        "owner": ""
                    },
                    "name": "newVariable",
                    "status": "incomplete",
                    "summary": "Create a Job Variable",
                    "type": "operation",
                    "variables": {
                        "incoming": {
                            "name": "run_time",
                            "value": {
                                "value_output": "I am RunTime Variable"
                            }
                        },
                        "outgoing": {
                            "value": 'null'
                        }
                    },
                    "x": 0.45615384615384613,
                    "y": -0.04755043227665706
                },
                "workflow_end": {
                    "groups": [],
                    "name": "workflow_end",
                    "status": "incomplete",
                    "x": 0.9,
                    "y": 0.5979827089337176
                },
                "workflow_start": {
                    "groups": [],
                    "metrics": {
                        "finish_state": "success",
                        "start_time": 1551043499742,
                        "user": "5b8fe4fcb3f8b800134ea5fd"
                    },
                    "name": "workflow_start",
                    "status": "complete",
                    "x": 0.04692307692307692,
                    "y": 0.6023054755043228
                }
            },
            "transitions": {
                "10d1": {
                    "5023": {
                        "state": "success",
                        "type": "standard"
                    }
                },
                "5023": {
                    "50c1": {
                        "state": "success",
                        "type": "standard"
                    }
                },
                "50c1": {
                    "f97e": {
                        "state": "success",
                        "type": "standard"
                    }
                },
                "7cd4": {
                    "workflow_end": {
                        "state": "success",
                        "type": "standard"
                    }
                },
                "87f4": {
                    "7cd4": {
                        "state": "success",
                        "type": "standard"
                    }
                },
                "f97e": {
                    "87f4": {
                        "state": "success",
                        "type": "standard"
                    }
                },
                "workflow_end": {},
                "workflow_start": {
                    "10d1": {
                        "state": "success",
                        "type": "standard"
                    }
                }
            },
            "type": "automation",
            "variables": {
                "_id": "e17646fc7a8f4a6a9e691fe4",
                "initiator": "admin@pronghorn",
                "value": "3333"
            },
            "watchers": [
                "5b8fe4fcb3f8b800134ea5fd"
            ]
        }
        result = iap_start_workflow.start_workflow(module)
        self.assertEquals(result, return_response)


if __name__ == '__main__':
    unittest.main()
