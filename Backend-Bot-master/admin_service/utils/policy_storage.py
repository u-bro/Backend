import os

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError


S3_AVATARS_BUCKET = os.getenv("S3_AVATARS_BUCKET", "ubro-avatar")


class PolicyStorage:
    def __init__(self) -> None:
        self.client = boto3.client(
            "s3",
            endpoint_url="https://s3.selcdn.ru",
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "test-aws-access-key-id"),
            aws_secret_access_key=os.getenv("AWS_SECRET_KEY", "test-aws-secret-access-key"),
            config=Config(signature_version="s3v4"),
        )

    def upload(self, policy_key: str, content: bytes, content_type: str = "application/pdf") -> None:
        storage_key = f"policy/{policy_key}"
        self.client.put_object(
            Bucket=S3_AVATARS_BUCKET,
            Key=storage_key,
            Body=content,
            ContentType=content_type,
            ContentDisposition=f'inline; filename="{policy_key}"',
        )

    def get(self, policy_key: str) -> tuple[bytes, str, str]:
        storage_key = f"policy/{policy_key}"
        try:
            obj = self.client.get_object(Bucket=S3_AVATARS_BUCKET, Key=storage_key)
        except ClientError as exc:
            if exc.response.get("Error", {}).get("Code") == "NoSuchKey":
                raise FileNotFoundError(storage_key) from exc
            raise

        return (
            obj["Body"].read(),
            obj.get("ContentType", "application/pdf"),
            obj.get("ContentDisposition", f'inline; filename="{policy_key}.pdf"'),
        )


policy_storage = PolicyStorage()
