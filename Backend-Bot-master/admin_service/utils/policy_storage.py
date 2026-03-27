from .s3_storage import S3_AVATARS_BUCKET, s3_storage


class PolicyStorage:
    def __init__(self) -> None:
        self.client = s3_storage.client

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
