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


## Findings

**September 2025 – September 2026, derived from raw balancing-market data:**

| | |
|---|---|
| Wind curtailed | **11.0 TWh** |
| Paid to wind farms | **£356.1m** |
| Average rate | **£32.28/MWh** |

Published estimates for calendar 2025 put curtailment at 10 TWh costing ~£343m
in payments to Scottish wind. This pipeline reproduces that independently to
within a few percent, over a window shifted later into a period where
curtailment has been rising ~22% year on year.

### What the data shows

- **Concentration.** Four wind farms — Moray East, Seagreen, Moray West and
  Viking — account for ~64% of all GB wind curtailment. All sit north of the
  Scottish transmission constraint.
- **It is constraints, not trading.** Of 1,642 wind balancing instructions on
  16 Sep 2026, 1,640 carried the system-operator flag. These units are in the
  balancing mechanism because the network is full.
- **Onshore costs more per MWh.** Whitelee and Kilgallioch were curtailed at
  £80–90/MWh against Moray's ~£30/MWh. Offshore dominates volume; onshore is
  dearer per unit.
- **Strong seasonality.** 33–38 units instructed per week in mid-July against
  90–120 through autumn and winter.

### Caveats

- Costs cover payments to wind only. Published headline figures (~£1.4bn for
  2025) also include the cost of replacement generation.
- Volume-only and priced runs differ by ~1.2%, as the priced calculation clips
  each measurement to a bid-offer window.

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
