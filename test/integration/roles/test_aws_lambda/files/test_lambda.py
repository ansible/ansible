import json


def handler(event, context):
    print("Incoming event: " + json.dumps(event))
    return { "status": "complete" }
