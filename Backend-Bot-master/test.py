import boto3
from botocore.exceptions import ClientError

s3 = boto3.client(
    "s3",
    endpoint_url="https://s3.selcdn.ru",
    aws_access_key_id="fc6fa8908694465499e65dd9f9d3a643",
    aws_secret_access_key="b8be0633a1764a82a6f0cc48161edb61",
)

try:
    resp = s3.list_buckets()
    print("Доступ есть")
    print([b["Name"] for b in resp.get("Buckets", [])])
except ClientError as e:
    print("Доступа нет")
    print(e)