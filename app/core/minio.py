import json
from datetime import timedelta
from uuid import uuid4

from minio import Minio

from app.core.config import settings

_client: Minio | None = None


def get_minio_client() -> Minio:
    global _client
    if _client is None:
        _client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
        )
    return _client


def ensure_bucket_exists() -> None:
    client = get_minio_client()
    if not client.bucket_exists(settings.minio_bucket):
        client.make_bucket(settings.minio_bucket)

    # Make avatars/ prefix publicly readable so stored URLs never expire.
    public_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"AWS": ["*"]},
                "Action": ["s3:GetObject"],
                "Resource": [f"arn:aws:s3:::{settings.minio_bucket}/avatars/*"],
            }
        ],
    }
    client.set_bucket_policy(settings.minio_bucket, json.dumps(public_policy))


def _make_object_key(filename: str, prefix: str | None) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    name = f"{uuid4()}.{ext}" if ext else str(uuid4())
    return f"{prefix}/{name}" if prefix else name


def avatar_public_url(object_key: str) -> str:
    scheme = "https" if settings.minio_secure else "http"
    return f"{scheme}://{settings.minio_endpoint}/{settings.minio_bucket}/{object_key}"


def generate_presigned_put_url(
    filename: str, prefix: str | None = None
) -> tuple[str, str]:
    object_key = _make_object_key(filename, prefix)
    url = get_minio_client().presigned_put_object(
        settings.minio_bucket,
        object_key,
        expires=timedelta(minutes=15),
    )
    return object_key, url


def generate_presigned_get_url(object_key: str) -> str:
    return get_minio_client().presigned_get_object(
        settings.minio_bucket,
        object_key,
        expires=timedelta(hours=1),
    )


def remove_object(object_key: str) -> None:
    get_minio_client().remove_object(settings.minio_bucket, object_key)
