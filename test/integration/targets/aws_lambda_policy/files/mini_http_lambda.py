from __future__ import print_function
import json


def handler(event, context):
    """
    The handler function is the function which gets called each time
    the lambda is run.
    """
    # printing goes to the cloudwatch log allowing us to simply debug the lambda if we can find
    # the log entry.
    print("got event:\n" + json.dumps(event))

    # if the name parameter isn't present this can throw an exception
    # which will result in an amazon chosen failure from the lambda
    # which can be completely fine.

    name = event["pathParameters"]["greet_name"]

    return {"statusCode": 200,
            "body": 'hello: "' + name + '"',
            "headers": {}}


def main():
    """
    This main function will normally never be called during normal
    lambda use.  It is here for testing the lambda program only.
    """
    event = {"name": "james"}
    context = None
    print(handler(event, context))


if __name__ == '__main__':
    main()
