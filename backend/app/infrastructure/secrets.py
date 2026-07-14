import os
from app.domain.interfaces import ISecretsManager

class EnvSecretsManager(ISecretsManager):
    """Local secrets manager wrapping os.environ.
    Enterprise version would integrate with HashiCorp Vault or AWS Secrets Manager."""

    def get_secret(self, key: str) -> str | None:
        return os.environ.get(key)
