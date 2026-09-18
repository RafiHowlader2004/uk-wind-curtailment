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

## Status

Work in progress.

- [x] Elexon API exploration; BOALF to unit-registry join verified
- [ ] Curtailment calculation
- [ ] Validation against published figures
- [ ] Historical backfill into DuckDB
- [ ] Automated daily ingest
- [ ] Published dashboard

## Data sources

- [Elexon BMRS](https://bmrs.elexon.co.uk/) — balancing market data (no API key required)

## Running it

    python -m venv .venv && source .venv/bin/activate
    pip install -r requirements.txt
