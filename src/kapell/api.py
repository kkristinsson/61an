import os
import requests
from dotenv import load_dotenv
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

load_dotenv()

BASE_URL = "https://ext-api.vasttrafik.se/pr/v4"
TOKEN_URL = "https://ext-api.vasttrafik.se/token"


@dataclass
class Location:
    gid: str
    name: str
    lat: Optional[float] = None
    lon: Optional[float] = None


@dataclass
class Departure:
    line: str
    planned_time: datetime
    estimated_time: Optional[datetime]
    platform: Optional[str]
    is_cancelled: bool
    is_part_cancelled: bool
    direction: Optional[str]


class VasttrafikAPI:
    def __init__(self):
        self.client_id = os.getenv("VASTTRAFIK_CLIENT_ID")
        self.client_secret = os.getenv("VASTTRAFIK_CLIENT_SECRET")
        if not self.client_id or not self.client_secret:
            raise ValueError("Missing VASTTRAFIK_CLIENT_ID or CLIENT_SECRET in .env")
        self.session = requests.Session()
        self._get_token()

    def _get_token(self) -> None:
        resp = self.session.post(
            TOKEN_URL,
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            },
        )
        resp.raise_for_status()
        token = resp.json().get("access_token")
        if not token:
            raise Exception("Access token missing from response")
        self.session.headers["Authorization"] = f"Bearer {token}"

    def get_locations(self, query: str, location_type: str = "stoparea", limit: int = 1) -> List[Location]:
        """Search locations by text."""
        params = {"q": query, "types": [location_type], "limit": limit}
        resp = self.session.get(f"{BASE_URL}/locations/by-text", params=params)
        resp.raise_for_status()
        data: Dict[str, Any] = resp.json()
        results = []
        for loc in data.get("results", []):
            results.append(
                Location(
                    gid=loc["gid"],
                    name=loc["name"],
                    lat=loc.get("latitude"),
                    lon=loc.get("longitude"),
                )
            )
        return results

    def get_departures(
        self,
        origin_gid: str,
        direction: Optional[str] = None,
        direction_gid: Optional[str] = None,
        line_designation: str = "61",
        limit: int = 20,
        minutes: int = 60,
        start_datetime: Optional[datetime] = None,
    ) -> List[Departure]:
        """Get departures from origin."""
        params = {
            "limit": limit,
            "timeSpanInMinutes": minutes,
            "includeOccupancy": "true",
        }
        if start_datetime is not None:
            params["startDateTime"] = start_datetime.isoformat(timespec="seconds")
        if direction_gid:
            params["directionGid"] = direction_gid

        resp = self.session.get(f"{BASE_URL}/stop-areas/{origin_gid}/departures", params=params)
        resp.raise_for_status()
        data: Dict[str, Any] = resp.json()
        departures = []
        normalized_direction = direction.casefold() if direction else None

        for dep in data.get("results", []):
            sj = dep.get("serviceJourney", {})
            line = sj.get("line", {})
            designation = line.get("designation")
            if designation != line_designation:
                continue

            service_direction = sj.get("direction")
            if normalized_direction and (
                not service_direction or normalized_direction not in service_direction.casefold()
            ):
                continue

            planned_str = dep["plannedTime"]
            planned = datetime.fromisoformat(planned_str.replace("Z", "+00:00"))
            est_str = dep.get("estimatedTime")
            est = datetime.fromisoformat(est_str.replace("Z", "+00:00")) if est_str else None
            departures.append(
                Departure(
                    line=designation,
                    planned_time=planned,
                    estimated_time=est,
                    platform=dep.get("stopPoint", {}).get("name"),
                    is_cancelled=dep.get("cancelled", False),
                    is_part_cancelled=dep.get("partCancelled", False),
                    direction=service_direction,
                )
            )
        # Sort by best time (est > planned)
        departures.sort(key=lambda d: d.estimated_time or d.planned_time)
        return departures
