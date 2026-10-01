from monitoramento.environmental import AnalysisType, EnvironmentalReading, EnvironmentalStore
from monitoramento.payments import SimulatedUsdcProvider
from monitoramento.provenance import SimulatedSolanaProofProvider, dataset_hash


def test_environmental_ingestion_and_analysis():
    store = EnvironmentalStore()
    store.ingest(EnvironmentalReading.now("node-1", 0, 0, "vegetation", {"vegetation_coverage_percent": 80}, {"species": "jaguar"}))
    store.ingest(EnvironmentalReading.now("node-2", 0, .001, "vegetation", {"vegetation_coverage_percent": 90}, {"species": "tapir"}))
    result = store.analyze(AnalysisType.FOREST_HEALTH)
    assert result["vegetation_coverage_percent"] == 85
    assert store.analyze(AnalysisType.BIODIVERSITY)["species_count"] == 2


def test_proof_and_simulated_payment():
    proof = SimulatedSolanaProofProvider().register({"value": 1})
    assert proof.network == "solana-devnet"
    assert proof.dataset_hash == dataset_hash({"value": 1})
    assert SimulatedUsdcProvider().charge(2.5).status == "confirmed"
