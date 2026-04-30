# FRC Match Times — Setup & Usage Guide

This script connects to the [FRC Events API](https://frc-api.firstinspires.org) and displays match timing information (scheduled start, actual start, actual end, and duration) for every played match at a given event.

---

## Prerequisites

- Python 3.11 or newer
- An FRC Events API account ([register here](https://frc-api.firstinspires.org))
- Your API **username** and **authorization token**

---

## Running in a Virtual Environment

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
| Windows (cmd) | `.venv\Scripts\activate.bat` |
| Windows (PowerShell) | `.venv\Scripts\Activate.ps1` |

You should see `(.venv)` prepended to your shell prompt once activated.

### 4. Install dependencies

```bash
pip install requests
```

### 5. Run the script

Pass your FRC API credentials as command-line arguments:

```bash
python frc_match_times.py --year 2024 --event TXHOU --username YOUR_USERNAME --token YOUR_TOKEN
```

Or export them as environment variables and omit the flags:

```bash
export FRC_API_USERNAME=YOUR_USERNAME
export FRC_API_TOKEN=YOUR_TOKEN

python frc_match_times.py --year 2024 --event TXHOU
```

> **Windows (PowerShell):** use `$env:FRC_API_USERNAME = "YOUR_USERNAME"` instead of `export`.

---

## Command-Line Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `--year` | ✅ | Four-digit season year, e.g. `2024` |
| `--event` | ✅ | Event code, e.g. `TXHOU` |
| `--username` | ✅* | FRC API username (`FRC_API_USERNAME` env var also accepted) |
| `--token` | ✅* | FRC API token (`FRC_API_TOKEN` env var also accepted) |

\* Required unless the corresponding environment variable is set.

---

## Example Output

```
FRC 2024 Event: TXHOU
============================================================

  Qualification Matches
  -----------------------------------------------------------------------
  Match  Scheduled Start            Actual Start               Actual End                 Duration
  -----------------------------------------------------------------------
  1      2024-03-08 09:00:00 UTC    2024-03-08 09:02:15 UTC    2024-03-08 09:04:30 UTC    2m 15s
  2      2024-03-08 09:08:00 UTC    2024-03-08 09:10:05 UTC    2024-03-08 09:12:22 UTC    2m 17s
  ...

  Playoff Matches
  -----------------------------------------------------------------------
  Match  Scheduled Start            Actual Start               Actual End                 Duration
  -----------------------------------------------------------------------
  1      2024-03-09 09:00:00 UTC    2024-03-09 09:03:40 UTC    2024-03-09 09:06:01 UTC    2m 21s
  ...
```

---

## Deactivating the Virtual Environment

When you are done, deactivate the virtual environment:

```bash
deactivate
```
