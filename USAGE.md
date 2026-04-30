# FRC Match Times – Usage Guide

This script connects to the [FRC Events API](https://frc-events.firstinspires.org/services/API)
and pulls all played matches for a given event, showing:

* **Scheduled Start** – the originally planned start time for the match
* **Actual Start** – the time the match actually began
* **Actual End** – the time results were posted (post-result time)
* **Duration** – elapsed time between actual start and actual end

---

## Prerequisites

* Python 3.10 or later
* An FRC Events API account – register at <https://frc-events.firstinspires.org/services/API>

---

## Setting Up a Virtual Environment

### 1. Clone / download the repository

```bash
git clone https://github.com/schnabel45/frc-scripts.git
cd frc-scripts
```

### 2. Create a virtual environment

```bash
python3 -m venv .venv
```

### 3. Activate the virtual environment

| Platform | Command |
|----------|---------|
| macOS / Linux | `source .venv/bin/activate` |
| Windows (PowerShell) | `.venv\Scripts\Activate.ps1` |
| Windows (cmd.exe) | `.venv\Scripts\activate.bat` |

You should see `(.venv)` prepended to your shell prompt.

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

---

## Configuration – API Credentials

The script requires a **username** and **API token** from the FRC Events API.

The recommended approach is to set environment variables so credentials are never
passed on the command line:

```bash
export FRC_API_USERNAME="your_username"
export FRC_API_TOKEN="your_token"
```

On Windows PowerShell:

```powershell
$Env:FRC_API_USERNAME = "your_username"
$Env:FRC_API_TOKEN    = "your_token"
```

Alternatively, you can pass credentials directly via flags (see below).

---

## Running the Script

```
python frc_match_times.py --year <YEAR> --event <EVENT_CODE>
```

### Arguments

| Argument | Required | Description |
|---|---|---|
| `--year` | Yes | Four-digit season year, e.g. `2024` |
| `--event` | Yes | FRC event code, e.g. `WAELL` |
| `--username` | No | API username (overrides `FRC_API_USERNAME` env var) |
| `--token` | No | API token (overrides `FRC_API_TOKEN` env var) |

### Examples

Using environment variables (recommended):

```bash
python frc_match_times.py --year 2024 --event WAELL
```

Passing credentials directly:

```bash
python frc_match_times.py --year 2024 --event WAELL \
    --username myuser --token mytoken
```

---

## Sample Output

```
FRC 2024 Event: WAELL
Fetching match data for all levels...

============================================================
  Practice Matches
============================================================
  Match     Scheduled Start      Actual Start         Actual End           Duration
  --------------------------------------------------------------------------
  1         2024-03-08 08:00:00  2024-03-08 08:03:12  2024-03-08 08:05:47  2m 35s
  2         2024-03-08 08:08:00  2024-03-08 08:09:05  2024-03-08 08:11:30  2m 25s

============================================================
  Qualification Matches
============================================================
  Match     Scheduled Start      Actual Start         Actual End           Duration
  --------------------------------------------------------------------------
  1         2024-03-08 09:00:00  2024-03-08 09:01:45  2024-03-08 09:04:10  2m 25s
  ...

Total played matches shown: 82
```

---

## Deactivating the Virtual Environment

When finished, deactivate with:

```bash
deactivate
```
