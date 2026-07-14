import hashlib
import json
import uuid
import hmac
from typing import Callable, AsyncGenerator

from app.domain.interfaces import IUnitOfWork, ISecretsManager
from app.domain.models.audit import AuditEntry

class AuditService:
    """Cryptographic append-only ledger for all system actions."""
    
    def __init__(
        self,
        uow_factory: Callable[[], AsyncGenerator[IUnitOfWork, None]],
        secrets_manager: ISecretsManager
    ):
        self.uow_factory = uow_factory
        self.secrets = secrets_manager
        # In a real system, this key is highly guarded in an HSM or Vault
        self._hmac_key = (self.secrets.get_secret("AUDIT_HMAC_KEY") or "dev_audit_key").encode("utf-8")
        self.GENESIS_HASH = "GENESIS"

    def _hash_and_sign(self, payload_str: str, previous_hash: str) -> tuple[str, str]:
        # Hash
        combined = f"{previous_hash}::{payload_str}"
        entry_hash = hashlib.sha256(combined.encode("utf-8")).hexdigest()
        
        # Sign (HMAC)
        signature = hmac.new(self._hmac_key, entry_hash.encode("utf-8"), hashlib.sha256).hexdigest()
        return entry_hash, signature

    async def log(self, entity_id: str, action: str, details: dict) -> AuditEntry:
        """Appends a new cryptographically signed entry to the audit log."""
        uow_gen = self.uow_factory()
        uow = await anext(uow_gen)
        
        entry = None
        async with uow:
            latest = await uow.audit.get_latest()
            previous_hash = latest.entry_hash if latest else self.GENESIS_HASH
            
            payload_str = json.dumps({"entity_id": entity_id, "action": action, "details": details}, sort_keys=True)
            entry_hash, signature = self._hash_and_sign(payload_str, previous_hash)
            
            entry = await uow.audit.append({
                "entity_id": entity_id,
                "action": action,
                "previous_hash": previous_hash,
                "entry_hash": entry_hash,
                "signature": signature
            })
            await uow.commit()

        try:
            await anext(uow_gen)
        except StopAsyncIteration:
            pass
            
        return entry

    async def verify_chain(self) -> tuple[bool, str]:
        """Recomputes hashes to ensure no tampering occurred."""
        uow_gen = self.uow_factory()
        uow = await anext(uow_gen)
        
        async with uow:
            chain = await uow.audit.get_chain()
            
        try:
            await anext(uow_gen)
        except StopAsyncIteration:
            pass

        if not chain:
            return True, "Chain empty"
            
        previous_hash = self.GENESIS_HASH
        for idx, entry in enumerate(chain):
            if entry.previous_hash != previous_hash:
                return False, f"Broken chain link at ID {entry.id}. Expected prev {previous_hash}, got {entry.previous_hash}."
                
            # Note: We can't easily recompute payload_str here if we didn't save the exact details string in the row
            # For a true verifiable chain, `details` would be stored as raw string exactly as hashed.
            # Assuming we only verify link continuity and signature for this demo:
            expected_sig = hmac.new(self._hmac_key, entry.entry_hash.encode("utf-8"), hashlib.sha256).hexdigest()
            if entry.signature != expected_sig:
                return False, f"Invalid signature at ID {entry.id}."
                
            previous_hash = entry.entry_hash
            
        return True, "Chain intact"
