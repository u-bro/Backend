import os

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError


S3_DOCUMENTS_BUCKET = os.getenv("S3_DOCUMENTS_BUCKET", "ubro-documents")
S3_AVATARS_BUCKET = os.getenv("S3_AVATARS_BUCKET", "ubro-avatar")


class S3Storage:
    def __init__(self) -> None:
        self.client = boto3.client(
            "s3",
            endpoint_url="https://s3.selcdn.ru",
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "test-aws-access-key-id"),
            aws_secret_access_key=os.getenv("AWS_SECRET_KEY", "test-aws-secret-access-key"),
            config=Config(signature_version="s3v4"),
        )

    def get_object(self, key: str, bucket: str = S3_DOCUMENTS_BUCKET) -> tuple[bytes, str, str]:
        try:
            obj = self.client.get_object(Bucket=bucket, Key=key)
        except ClientError as exc:
            if exc.response.get("Error", {}).get("Code") == "NoSuchKey":
                raise FileNotFoundError(key) from exc
            raise

        return (
            obj["Body"].read(),
            obj.get("ContentType", "application/octet-stream"),
            obj.get("ContentDisposition", f'inline; filename="{key.split("/")[-1]}"'),
        )

    def presigned_get_url(self, key: str, bucket: str = S3_DOCUMENTS_BUCKET, expires_seconds: int = 3600) -> str:
        return self.client.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=expires_seconds,
        )


s3_storage = S3Storage()
