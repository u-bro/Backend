import anyio, boto3
from app.config import S3_DOCUMENTS_BUCKET, AWS_REGION, AWS_ACCESS_KEY, AWS_SECRET_KEY


class CrudDocument:
    def __init__(self, bucket: str, region: str | None = None):
        self.bucket = bucket
        self.client = boto3.client("s3", region_name=region, aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY)

    def _put_object(self, key: str, pdf_bytes: bytes, metadata: dict | None = None) -> None:
        extra: dict = {
            "ContentType": "application/pdf",
            "ContentDisposition": f'inline; filename="{key.split("/")[-1]}"',
        }
        if metadata:
            extra["Metadata"] = {k: str(v) for k, v in metadata.items()}

        self.client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=pdf_bytes,
            **extra,
        )

    def _get_object_bytes(self, key: str) -> bytes:
        obj = self.client.get_object(Bucket=self.bucket, Key=key)
        return obj["Body"].read()

    def _delete_object(self, key: str) -> None:
        self.client.delete_object(Bucket=self.bucket, Key=key)

    async def upload_pdf_bytes(self, key: str, pdf_bytes: bytes, metadata: dict | None = None) -> None:
        await anyio.to_thread.run_sync(
            self._put_object,
            key,
            pdf_bytes,
            metadata,
        )

    async def get_pdf_bytes(self, key: str) -> bytes:
        return await anyio.to_thread.run_sync(self._get_object_bytes, key)

    async def delete_by_key(self, key: str) -> None:
        await anyio.to_thread.run_sync(self._delete_object, key)

    def presigned_get_url(self, key: str, expires_seconds: int = 3600) -> str:
        return self.client.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=expires_seconds,
        )

    def public_url(self, key: str) -> str:
        region = self.client.meta.region_name
        if region:
            return f"https://{self.bucket}.s3.{region}.amazonaws.com/{key}"
        return f"https://{self.bucket}.s3.amazonaws.com/{key}"

    async def create(self, key: str, pdf_bytes: bytes, metadata: dict | None = None) -> None:
        return await self.upload_pdf_bytes(key, pdf_bytes, metadata=metadata)

    async def get_by_key(self, key: str) -> bytes:
        return await self.get_pdf_bytes(key)

    async def delete(self, key: str) -> None:
        return await self.delete_by_key(key)


document_crud = CrudDocument(bucket=S3_DOCUMENTS_BUCKET, region=AWS_REGION)
