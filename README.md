# R.A.M.A.

## Decentralized Environmental Intelligence Network

R.A.M.A. (Autonomous Environmental Monitoring Network) is a decentralized environmental intelligence platform that combines monitoring nodes, aerial data collection, environmental analysis, and verifiable on-chain records.

Organizations can request and pay for forest health, terrain, and biodiversity analyses. Environmental datasets remain off-chain while Solana provides data provenance, integrity verification, and payments.

The environmental mission comes first. Blockchain and AI are infrastructure that make the product verifiable and useful.

## Crypto World's Fair 2026 MVP

The hackathon MVP prioritizes a working end-to-end demonstration over the complete physical infrastructure described in the long-term vision.

```text
Monitoring Node → Environmental Data → R.A.M.A. Backend
       → Analysis → Dataset Hash → Solana Proof
       → Payment / Customer → Environmental Report
```

An organization should be able to select an area, choose an analysis, request and pay for it, receive a result, and verify its provenance on Solana Devnet.

## Initial environmental products

### Forest Health

- Vegetation coverage
- General forest condition
- Vegetation change or degradation
- Relevant environmental indicators

### Terrain Analysis

- Topography
- Elevation
- Slope
- General terrain characteristics

### Biodiversity Analysis

- Observed or detected species
- Biodiversity records
- Aggregated indicators for the monitored area

Public datasets, fixtures, or simulated data may be used when real data or complete scientific models are not feasible within the hackathon timeline. Simulated data must always be identified as simulated.

## Architecture

```text
Environmental Area
    ↓
Sensors, Monitoring Nodes, and Aerial Data
    ↓
R.A.M.A. Network
    ↓
Off-chain Data Processing
    ↓
AI and Environmental Analysis
    ↓
Environmental Intelligence Product
    ↓
Blockchain Verification
    ↓
Customer or Organization
```

The MVP represents at least three independent monitoring nodes. They may initially be simulated, but the node interface is designed so real Raspberry Pi devices and environmental sensors can replace them later.

Each node produces structured data that may include `node_id`, timestamp, geographic location, sensor or data type, measurements, and metadata. Complete datasets, images, and analysis artifacts remain in appropriate off-chain storage.

## Solana integration

The MVP uses Solana Devnet. Solana is not used as the primary database for telemetry or images.

1. **Data provenance:** prove that a dataset or result existed at a given time and was associated with a monitoring node.
2. **Integrity verification:** record a dataset or analysis hash on-chain so later changes can be detected.
3. **Payments:** associate an analysis request with a Solana payment, preferably in USDC when feasible.

```text
Dataset → Cryptographic Hash → Solana Transaction → Verification
```

The MVP does not introduce a proprietary token.

## User experience

```text
Select Region

Analysis:
[ ] Forest Health
[ ] Terrain Analysis
[ ] Biodiversity Analysis

Estimated cost: X USDC

[ Request Analysis ]
```

Results should include the monitored area, environmental indicators, analysis date, data source, and a clear `VERIFIED ON SOLANA` action that opens the blockchain proof.

## Technology direction

- Python for ingestion, mission, and analysis services
- Raspberry Pi as the physical monitoring-node reference platform
- FastAPI when an API or backend service is required
- Environmental sensors and simulated node adapters
- Off-chain database and object storage
- Computer vision or AI when it adds clear value
- Solana Devnet and USDC when technically feasible
- A simple web dashboard for the demonstration

The project avoids additional technologies unless they solve a specific MVP requirement.

## Scope priorities

### Must have

- Three identifiable monitoring nodes
- Structured environmental data ingestion
- Off-chain dataset storage
- Cryptographic dataset or result hashing
- Solana proof registration and verification
- Forest Health, Terrain Analysis, and Biodiversity Analysis flows
- Analysis request interface
- Demonstrable payment flow when feasible
- Environmental intelligence dashboard

### Should have

- Public datasets with clear source attribution
- A Raspberry Pi-ready node adapter boundary
- Analysis history and request status
- Direct links to Solana proofs
- A concise hackathon demo mode

### Could have

- Live Raspberry Pi sensor input
- Image upload and map visualization
- More detailed AI-assisted interpretation
- Automatic payment splitting in a controlled demonstration

### Post-hackathon

Fire detection, air quality, microclimate, water resources, deforestation, historical change, agriculture, coastal monitoring, physical drone fleets, VTOL aircraft, real flight control, large-scale mesh networking, autonomous towers, docking infrastructure, node incentives, reputation, a DAO, and a decentralized marketplace.

## Long-term vision

The original R.A.M.A. vision remains part of the project. It describes a distributed environmental monitoring infrastructure made of autonomous stations, Raspberry Pi computers, environmental sensors, mesh communication, and drones operating where continuous human intervention is difficult.

The future system may include solar-powered autonomous towers with drone docks, a staffed field base, resilient communications, aerial patrol missions, RGB and thermal imaging, GNSS, environmental telemetry, and a central operations platform.

The hackathon MVP is a focused product slice of that vision. It proves that monitoring data can become a useful environmental intelligence product with transparent provenance and a viable payment path. It does not attempt to build the complete physical infrastructure.

## Out of scope for the MVP

- Complete physical drone fleet or autonomous flight
- Real flight control, VTOL aircraft, or drone operations
- Full-scale physical mesh networking
- Tower construction or industrial hardware
- Deployment in a real forest
- Mass image processing or complete scientific biodiversity models
- Proprietary token, DAO, or complete network economy
- Complex marketplace or multiple blockchains
- Production-scale infrastructure

## Project status

The repository currently contains the initial Python mission and route-planning foundation, including simulated mission execution, route generation, telemetry models, and battery-triggered return-to-base behavior.

The next implementation phase is the hackathon MVP: node simulation, data ingestion, off-chain analysis, Solana proof verification, payments, and the demonstration dashboard.

## Repository contents

- `src/monitoramento/` — initial mission and route-planning code
- `tests/` — automated checks for the mission foundation
- `Sistema_Integrado_de_Monitoramento_Ambiental.docx` — original technical vision document
- `img/` — project reference images
- `pyproject.toml` — Python project configuration

## Local simulation

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
python -m monitoramento.cli --demo
```

## Local API and dashboard

Install the optional web dependencies and start the simulation API:

```powershell
pip install -e ".[web]"
uvicorn monitoramento.main:app --reload
```

The API exposes mission creation, validation, simulation control, telemetry, events, reports, GeoJSON route generation, environmental readings, analysis, simulated Solana provenance, and simulated USDC payments. The lightweight dashboard is in `dashboard/index.html` and intentionally focuses on a navigation-chart view instead of a decorative interface.

The simulator does not connect to a real aircraft. Physical flight operation must keep the flight controller responsible for stabilization, navigation, and safety procedures.

## Project positioning

Primary category: **Climate / Green Tech**

Associated categories: **Environmental Intelligence, DePIN, Payments, Developer Infrastructure, and AI**

Target users include companies, environmental organizations, NGOs, researchers, universities, governments, protected-area managers, and organizations that need environmental intelligence for conservation or ESG decisions.
