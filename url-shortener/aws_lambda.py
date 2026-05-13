# initial design built as AWS Lambda function

"""
1. user clicks short URL
2. API Gateway receives GET /url/{shortKey}
3. API Gateway triggers AWS Lambda
4. Lambda reads shortKey from event["pathParameters"]
5. Lambda queries RDS MySQL using pymysql
6. Lambda returns 302 redirect with Location: longUrl
7. browser opens the real long URL
"""

import os
import json
import pymysql


def get_read_db_connection_cursor():
    conn = pymysql.connect(
        host=os.environ["DB_HOST"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        database=os.environ["DB_NAME"],
        connect_timeout=5,
    )
    return conn, conn.cursor()


def fetch_long_url(short_key):
    conn, cursor = get_read_db_connection_cursor()

    try:
        cursor.execute(
            "SELECT longUrl FROM Urls WHERE shortKey = %s LIMIT 1",
            (short_key,)
        )

        result = cursor.fetchone()

        if not result:
            return None

        long_url = result[0]

        if isinstance(long_url, bytes):
            long_url = long_url.decode()

        return long_url

    finally:
        cursor.close()
        conn.close()


def lambda_handler(event, context):
    path_params = event.get("pathParameters") or {}
    short_key = path_params.get("shortKey")

    if not short_key:
        return {
            "statusCode": 400,
            "body": json.dumps({
                "message": "Error: shortKey is required."
            })
        }

    try:
        long_url = fetch_long_url(short_key)

        if not long_url:
            return {
                "statusCode": 404,
                "body": json.dumps({
                    "message": "Long URL for the provided shortKey was not found."
                })
            }

        return {
            "statusCode": 302,
            "headers": {
                "Location": long_url
            },
            "body": ""
        }

    except pymysql.MySQLError as e:
        return {
            "statusCode": 500,
            "body": json.dumps({
                "message": f"Database error: {str(e)}"
            })
        }


if __name__ == "__main__":
    event = {
        "pathParameters": {
            "shortKey": "xyz321"
        }
    }

    res = lambda_handler(event, None)
    print(res)