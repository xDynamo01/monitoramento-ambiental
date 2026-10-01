from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class Payment:
    payment_id: str
    amount_usdc: float
    status: str
    simulated: bool


class PaymentProvider(Protocol):
    def charge(self, amount_usdc: float) -> Payment: ...


class SimulatedUsdcProvider:
    def charge(self, amount_usdc: float) -> Payment:
        if amount_usdc <= 0:
            raise ValueError("o valor deve ser positivo")
        return Payment(f"sim-payment-{int(amount_usdc * 100)}", amount_usdc, "confirmed", True)


class SolanaUsdcProvider:
    def charge(self, amount_usdc: float) -> Payment:
        raise NotImplementedError("configure a carteira Solana antes do pagamento real")
