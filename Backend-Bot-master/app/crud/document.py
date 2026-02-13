import anyio, boto3
from botocore.exceptions import ClientError
from fastapi import HTTPException
from app.config import AWS_ACCESS_KEY_ID, AWS_SECRET_KEY
from app.enum import S3Bucket
from botocore.config import Config


class DocumentCrud:
    def __init__(self):
        self.client = boto3.client("s3", endpoint_url="https://s3.selcdn.ru", aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_KEY, config=Config(signature_version="s3v4"))

    def _put_object(self, key: str, pdf_bytes: bytes, content_type: str, metadata: dict | None = None, bucket: str = S3Bucket.DOCUMENT) -> None:
        extra: dict = {
            "ContentType": content_type,
            "ContentDisposition": f'inline; filename="{key.split("/")[-1]}"',
        }
        if metadata:
            extra["Metadata"] = {k: str(v) for k, v in metadata.items()}

        self.client.put_object(
            Bucket=bucket,
            Key=key,
            Body=pdf_bytes,
            **extra,
        )

    def _get_object_bytes(self, key: str, bucket: str = S3Bucket.DOCUMENT) -> bytes:
        try:
            obj = self.client.get_object(Bucket=bucket, Key=key)
            return obj["Body"].read()
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                raise HTTPException(status_code=404, detail="Document not found")
            raise HTTPException(status_code=500, detail=f"Error getting object: {e}")

    def _delete_object(self, key: str, bucket: str = S3Bucket.DOCUMENT) -> None:
        self.client.delete_object(Bucket=bucket, Key=key)

    async def upload_bytes(self, key: str, pdf_bytes: bytes, content_type: str = "application/pdf", metadata: dict | None = None, bucket: str = S3Bucket.DOCUMENT) -> None:
        await anyio.to_thread.run_sync(
            self._put_object,
            key,
            pdf_bytes,
            content_type,
            metadata,
            bucket,
        )

    async def get_pdf_bytes(self, key: str, bucket: str = S3Bucket.DOCUMENT) -> bytes:
        return await anyio.to_thread.run_sync(self._get_object_bytes, key, bucket)

    async def delete_by_key(self, key: str, bucket: str = S3Bucket.DOCUMENT) -> None:
        await anyio.to_thread.run_sync(self._delete_object, key, bucket)

    def presigned_get_url(self, key: str, expires_seconds: int = 3600, bucket: str = S3Bucket.DOCUMENT) -> str:
        return self.client.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=expires_seconds,
        )

    def public_url(self, key: str, bucket: str = S3Bucket.DOCUMENT) -> str:
        return f"https://{bucket}.s3.selcdn.ru/{key}"

    async def create(self, key: str, pdf_bytes: bytes, content_type: str = "application/pdf", metadata: dict | None = None, bucket: str = S3Bucket.DOCUMENT) -> None:
        return await self.upload_bytes(key, pdf_bytes, content_type=content_type, metadata=metadata, bucket=bucket)

    async def get_by_key(self, key: str, bucket: str = S3Bucket.DOCUMENT) -> bytes:
        return await self.get_pdf_bytes(key, bucket=bucket)

    async def delete(self, key: str, bucket: str = S3Bucket.DOCUMENT) -> None:
        return await self.delete_by_key(key, bucket=bucket)


document_crud = DocumentCrud()
