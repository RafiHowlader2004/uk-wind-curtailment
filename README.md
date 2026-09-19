# UK Wind Curtailment Tracker

Measuring how much Scottish wind generation is thrown away because the
transmission network can't carry it south — and what that costs bill payers.

## The problem

Britain's windiest regions are in Scotland. The transmission capacity between
Scotland and England is limited. When it's windy, wind farms are instructed to
reduce output, and are compensated for the energy they don't produce. Gas plants
further south are then paid to make up the shortfall. Consumers pay for both.

Nobody publishes "curtailment" as a number. It has to be derived from the
balancing market data.

## Method

For each wind farm, every half hour:

- **PN** (Physical Notification) — what the farm planned to generate
- **BOALF** (Bid-Offer Acceptance) — what the grid operator instructed instead
- **Curtailment** = the area between those two lines, in MWh

Both come from Elexon's public BMRS API.


## Findings so far

Sampled 15 Aug – 15 Sep 2026 (32 days), derived from raw balancing-market data:

| | |
|---|---|
| Wind curtailed | **905 GWh** over 32 days (~28.3 GWh/day) |
| Annualised | **~10.3 TWh/year** — published estimate for 2025 is 10 TWh |
| Concentration | **4 farms = 64%** of all GB wind curtailment |
| Worst single day | 4 Sep 2026: 127 GWh, costing **£5.9m** (£46.50/MWh) |

Top curtailed operators: Moray East (22%), Seagreen (22%), Moray West (14%),
Viking (6%) — all north of the Scottish transmission constraint.

Two further observations:

- **Wind balancing is almost entirely constraint-driven.** Of 1,642 wind
  instructions on 16 Sep, 1,640 carried the system-operator flag. These units
  are in the balancing mechanism because the network is full, not to trade.
- **Onshore rates exceed offshore.** Whitelee and Kilgallioch were curtailed at
  £80–90/MWh against Moray's ~£30/MWh. Offshore dominates volume; onshore is
  dearer per MWh.

### Caveats

- Volume and cost are computed slightly differently: the cost calculation clips
  each measurement to a bid-offer window, giving 127,451 MWh for 4 Sep against
  129,025 MWh from the volume-only run — a 1.2% difference.
- Costs cover payments to wind only. Published headline figures (~£1.4bn for
  2025) also include the cost of replacement generation.
- An annual cost figure needs the priced calculation run across a full year;
  scaling up from one extreme day overstates it.

## Status

Work in progress.

- [x] Elexon API exploration; BOALF to unit-registry join verified
- [x] Curtailment calculation
- [x] Validation against published figures (volume within 3%)
- [x] Historical backfill into DuckDB
- [ ] Priced backfill across a full year
- [ ] Automated daily ingest
- [ ] Published dashboard

## Data sources

- [Elexon BMRS](https://bmrs.elexon.co.uk/) — balancing market data (no API key required)

## Running it

    python -m venv .venv && source .venv/bin/activate
    pip install -r requirements.txt
