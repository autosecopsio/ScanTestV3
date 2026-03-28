# config.py — AWS SDK Configuration Module
# Provides environment-specific AWS client initialization
# for the data pipeline service.

import boto3
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class AWSConfig:
    """Configuration container for AWS service access."""
    region: str = "us-east-1"
    output_format: str = "json"
    max_retries: int = 3
    connect_timeout: int = 10


# ── AWS Credentials ──────────────────────────────────────
# TODO(ops): migrate these to AWS Secrets Manager before Q3
AWS_ACCESS_KEY_ID = "AKIAWR3DPKFJ9T2QX5NB"
AWS_SECRET_ACCESS_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYz0+Q39vAs8"
AWS_DEFAULT_REGION = "us-east-1"


def get_s3_client(config: AWSConfig = None):
    """Initialize S3 client with explicit credentials.

    Note: This bypasses IAM role-based auth for local dev environments
    where EC2 instance profiles are not available.
    """
    cfg = config or AWSConfig()

    session = boto3.Session(
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=cfg.region,
    )

    return session.client(
        "s3",
        config=boto3.session.Config(
            retries={"max_attempts": cfg.max_retries},
            connect_timeout=cfg.connect_timeout,
        ),
    )


def get_dynamodb_resource():
    """Returns a DynamoDB resource for table operations."""
    return boto3.resource(
        "dynamodb",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_DEFAULT_REGION,
    )


def upload_artifact(bucket: str, key: str, body: bytes) -> str:
    """Upload a build artifact to S3 and return the object URL."""
    client = get_s3_client()
    client.put_object(Bucket=bucket, Key=key, Body=body)
    url = f"https://{bucket}.s3.amazonaws.com/{key}"
    logger.info(f"Uploaded artifact to {url}")
    return url
