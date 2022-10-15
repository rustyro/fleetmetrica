import json
from cli.service import CLI, parser


def fleetmocker(event, context):
    parsed_args = parser.parse_args(event.split())
    resp = CLI(parsed_args).run()
    body = {
        "message": "Mocks successfully generated!",
        "input": event,
        "resp": resp
    }
    response = {
        "statusCode": 200,
        "body": json.dumps(body)
    }

    return response
