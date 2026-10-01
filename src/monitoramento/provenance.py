"""Dataset hashing and Solana-proof adapter for the MVP."""

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol


@dataclass(frozen=True)
class DatasetProof:
    dataset_hash: str
    network: str
    transaction_id: str
    created_at: datetime
    simulated: bool

    def to_dict(self):
        return {"dataset_hash": self.dataset_hash, "network": self.network, "transaction_id": self.transaction_id, "created_at": self.created_at.isoformat(), "simulated": self.simulated}


class ProofProvider(Protocol):
    def register(self, dataset: object) -> DatasetProof: ...


def dataset_hash(dataset: object) -> str:
    encoded = json.dumps(dataset, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


class SimulatedSolanaProofProvider:
    def register(self, dataset: object) -> DatasetProof:
        digest = dataset_hash(dataset)
        return DatasetProof(digest, "solana-devnet", f"sim-{digest[:32]}", datetime.now(timezone.utc), True)


class SolanaProofProvider:
    """Future RPC adapter; credentials and transaction submission stay external."""

    def register(self, dataset: object) -> DatasetProof:
        raise NotImplementedError("configure Solana RPC and wallet before live submission")
