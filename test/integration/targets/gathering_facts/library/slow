#!/bin/sh

sleep 10

echo '{
    "changed": false,
    "ansible_facts": {
        "factsone": "from slow module",
        "common_fact": "also from slow module",
		"common_dict_fact": {
			"key_one": "from slow ",
			"key_two": "from slow "
		},
		"common_list_fact": [
			"never",
			"does",
			"see"
		],
		"common_list_fact2": [
			"see",
			"does",
			"never",
			"theee"
		]
    }
}'
