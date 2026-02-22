# Kapell: Västtrafik Bus CLI

Kapell is a CLI tool for querying the next bus departures from Västtrafik (Swedish public transit). It wraps the Västtrafik PR v4 API to find bus 61 departures between locations.

## Architecture

**Core modules:**
- `api.py`: Västtrafik API client with OAuth2 token handling
- `cli.py`: Click-based CLI with `next` command
- `openapi.json`: API specification (reference only, not used by code)

**Data flow:**
1. User runs `kapell next <origin> <dest>`
2. CLI searches locations via `get_locations()` (text → GID)
3. CLI fetches departures via `get_departures()` with direction filtering
4. Results filtered to line 61, sorted by estimated/planned time

## API Integration

**Authentication:** OAuth2 client credentials flow
- Token fetched in `VasttrafikAPI.__init__()` via `_get_token()`
- Credentials loaded from `.env` via `python-dotenv`
- Required env vars: `VASTTRAFIK_CLIENT_ID`, `VASTTRAFIK_CLIENT_SECRET`

**Key endpoints:**
- `POST https://ext-api.vasttrafik.se/token` - Get OAuth token
- `GET /pr/v4/locations/by-text` - Search locations by name
- `GET /pr/v4/stop-areas/{gid}/departures` - Get departures with direction filtering

**Hardcoded behaviors:**
- Line filter: `designation == "61"` in `get_departures()` (line 99)
- Default timespan: 60 minutes
- Default limit: 20 departures, CLI displays top 3

## Development Setup

**Installation:**
```bash
pip install -e .  # Installs kapell command via setup.py entry_points
```

**Environment:** Create `.env` with Västtrafik API credentials:
```
VASTTRAFIK_CLIENT_ID=your_client_id
VASTTRAFIK_CLIENT_SECRET=your_client_secret
```

**Running:**
```bash
kapell next "Kapellplatsen" "Korsvägen"
```

## Code Patterns

**Dataclasses over dicts:** Use `@dataclass` for structured API responses (`Location`, `Departure`)

**DateTime handling:** Parse ISO 8601 strings, strip 'Z' suffix and use `fromisoformat()`:
```python
datetime.fromisoformat(time_str.replace("Z", "+00:00"))
```

**Session reuse:** `VasttrafikAPI` uses persistent `requests.Session` with Authorization header

**Error handling:** Relies on `resp.raise_for_status()` - no custom exception classes

**Type hints:** Use `Optional[T]` for nullable fields, `List[T]` for collections, explicit return types
