import json
from cli.service import CLI, parser
import config
from utils.s3 import S3


s3 = S3(aws_access_key_id=config.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY)


def fleetmocker(event, context):
    parsed_args = parser.parse_args(event.split())
    message = "Mocks successfully generated!"
    success, status = True, 200
    try:
        cli = CLI(parsed_args).run()
        upload_resp = s3.upload_directory(cli.store, config.S3_BUCKET_NAME)
        try:
            cli.flush_logs_to_db()
        except:
            print("error flushing logs")
            pass
    except Exception as e:
        message = str(e)
        success, status = False, 500

    resp = {}
    body = {
        "message": message,
        "input": event,
        "success": success
    }
    response = {
        "statusCode": status,
        "body": json.dumps(body)
    }

    return response
