import json
from io import BytesIO
from os import getenv

import boto3

s3 = boto3.resource("s3")
bucket = s3.Bucket(getenv("BUCKET_NAME"))


def handler(event, context):
    key = event["Records"][0]["cf"]["request"]["uri"]

    try:
        with BytesIO() as io:
            bucket.download_fileobj(key[1:], io)
            url = io.getvalue().decode().strip()

        return {
            "status": 307,
            "statusDescription": "Temporary Redirect",
            "headers": {"location": [{"key": "Location", "value": url}]},
            "body": f"Redirecionando para {url}",
        }

    except Exception as exc:
        return {
            "status": 404,
            "statusDescription": "Not Found",
            "headers": {
                "content-type": [{"key": "Content-Type", "value": "application/json"}]
            },
            "body": json.dumps(
                {
                    "message": "Link indisponível ou não encontrado",
                    "exc": str(exc),
                    "key": key,
                }
            ),
        }
