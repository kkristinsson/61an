from datetime import datetime
from typing import Any, Dict, List, Optional

from flask import Flask, render_template_string, request

from kapell.api import Location, VasttrafikAPI


PAGE_TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Kapell | Västtrafik Line 61</title>
  <style>
    :root {
      color-scheme: dark;
      --bg: #0f172a;
      --card: #111827;
      --muted: #94a3b8;
      --text: #e2e8f0;
      --accent: #22d3ee;
      --accent-2: #a78bfa;
      --ok: #34d399;
      --warn: #f59e0b;
      --danger: #fb7185;
      --border: #1f2937;
    }

    * { box-sizing: border-box; }

    body {
      margin: 0;
      min-height: 100vh;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
      background: radial-gradient(1200px 700px at 10% 0%, #1e293b 0%, var(--bg) 55%);
      color: var(--text);
      display: flex;
      justify-content: center;
      padding: 24px;
    }

    .app {
      width: 100%;
      max-width: 900px;
      background: linear-gradient(180deg, rgba(17,24,39,0.95), rgba(15,23,42,0.95));
      border: 1px solid var(--border);
      border-radius: 18px;
      padding: 20px;
      box-shadow: 0 24px 60px rgba(0,0,0,0.35);
    }

    h1 {
      margin: 0;
      font-size: 1.4rem;
      background: linear-gradient(90deg, var(--accent), var(--accent-2));
      -webkit-background-clip: text;
      background-clip: text;
      color: transparent;
    }

    .subtitle {
      margin: 8px 0 18px;
      color: var(--muted);
      font-size: 0.95rem;
    }

    .logo {
      margin: 0 0 10px;
      color: var(--accent);
      font-size: 0.8rem;
      line-height: 1.1;
      opacity: 0.95;
      user-select: none;
      white-space: pre;
    }

    .tabs {
      display: flex;
      gap: 8px;
      margin-bottom: 14px;
    }

    .tab {
      display: inline-block;
      text-decoration: none;
      color: var(--muted);
      border: 1px solid var(--border);
      background: rgba(15, 23, 42, 0.7);
      padding: 8px 12px;
      border-radius: 10px;
      font-size: 0.9rem;
    }

    .tab.active {
      color: var(--text);
      border-color: rgba(34, 211, 238, 0.45);
      background: rgba(2, 132, 199, 0.22);
    }

    form {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
      margin-bottom: 16px;
    }

    .full { grid-column: 1 / -1; }

    label {
      display: block;
      margin-bottom: 6px;
      font-size: 0.85rem;
      color: var(--muted);
    }

    input {
      width: 100%;
      background: #0b1220;
      color: var(--text);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 10px 12px;
      font-size: 0.95rem;
      outline: none;
    }

    input:focus {
      border-color: var(--accent);
      box-shadow: 0 0 0 3px rgba(34, 211, 238, 0.18);
    }

    button {
      border: 0;
      border-radius: 10px;
      background: linear-gradient(90deg, var(--accent), var(--accent-2));
      color: #0b1020;
      font-weight: 700;
      padding: 11px 14px;
      cursor: pointer;
      font-size: 0.95rem;
    }

    .alert {
      border-radius: 10px;
      padding: 10px 12px;
      margin: 10px 0 14px;
      border: 1px solid;
      font-size: 0.92rem;
    }

    .alert.error {
      border-color: rgba(251, 113, 133, 0.45);
      color: #fecdd3;
      background: rgba(127, 29, 29, 0.22);
    }

    .empty {
      border-color: rgba(245, 158, 11, 0.45);
      color: #fde68a;
      background: rgba(120, 53, 15, 0.22);
    }

    .info {
      border-color: rgba(34, 211, 238, 0.45);
      color: #bae6fd;
      background: rgba(2, 132, 199, 0.22);
    }

    .meta {
      margin: 8px 0 12px;
      color: var(--muted);
      font-size: 0.9rem;
    }

    .list {
      display: grid;
      gap: 10px;
      margin-top: 8px;
    }

    .item {
      background: rgba(15, 23, 42, 0.86);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 12px;
      display: grid;
      grid-template-columns: 100px 1fr auto;
      gap: 10px;
      align-items: center;
    }

    .time { font-size: 1.25rem; font-weight: 700; color: var(--ok); }
    .dir { color: var(--text); }
    .platform { color: var(--muted); font-size: 0.9rem; }
  </style>
</head>
<body>
  <main class="app">
    <pre class="logo"> /\_/\
(=^.^=)
(")_(")</pre>
    <h1>Kapell · Line 61</h1>
    <p class="subtitle">Search upcoming departures between two stop areas in Göteborg.</p>

    <nav class="tabs">
      <a class="tab {% if active_tab == 'search' %}active{% endif %}" href="/?tab=search">Search</a>
      <a class="tab {% if active_tab == 'next' %}active{% endif %}" href="/?tab=next">Next Rides</a>
    </nav>

    {% if active_tab == 'search' %}
    <form method="post">
      <input type="hidden" name="tab" value="search">
      <div>
        <label for="origin">Origin</label>
        <input id="origin" name="origin" value="{{ origin }}" placeholder="Kapellplatsen" required>
      </div>
      <div>
        <label for="destination">Destination</label>
        <input id="destination" name="destination" value="{{ destination }}" placeholder="Järntorget" required>
      </div>
      <div>
        <label for="count">Results</label>
        <input id="count" name="count" value="{{ count }}" type="number" min="1" max="20" required>
      </div>
      <div>
        <label for="date">Date</label>
        <input id="date" name="date" value="{{ date }}" type="date" required>
      </div>
      <div>
        <label for="time">Time</label>
        <input id="time" name="time" value="{{ time }}" type="time" required>
      </div>
      <div>
        <label for="minutes">Minutes Ahead</label>
        <input id="minutes" name="minutes" value="{{ minutes }}" type="number" min="1" max="180" required>
      </div>
      <div class="full">
        <button type="submit">Find Departures</button>
      </div>
    </form>
    {% else %}
    <form method="post">
      <input type="hidden" name="tab" value="next">
      <div>
        <label for="origin-fixed">Origin</label>
        <input id="origin-fixed" name="origin" value="Kapellplatsen" readonly>
      </div>
      <div>
        <label for="destination-fixed">Destination</label>
        <input id="destination-fixed" name="destination" value="Järntorget" readonly>
      </div>
      <div>
        <label for="count">Results</label>
        <input id="count" name="count" value="{{ count }}" type="number" min="1" max="20" required>
      </div>
      <div>
        <label for="date">Date</label>
        <input id="date" name="date" value="{{ date }}" type="date" required>
      </div>
      <div>
        <label for="time">Time</label>
        <input id="time" name="time" value="{{ time }}" type="time" required>
      </div>
      <div>
        <label for="minutes">Minutes Ahead</label>
        <input id="minutes" name="minutes" value="{{ minutes }}" type="number" min="1" max="180" required>
      </div>
      <div class="full">
        <button type="submit">Refresh Next Rides</button>
      </div>
    </form>
    {% endif %}

    {% if error %}
      <div class="alert error">{{ error }}</div>
    {% endif %}

    {% if searched and not departures and not error %}
      <div class="alert empty">No line 61 departures found for this route in the selected time window.</div>
    {% endif %}

    {% if fallback_used and departures %}
      <div class="alert info">No departures matched destination as terminal stop. Showing all line 61 departures from origin.</div>
    {% endif %}

    {% if departures %}
      <p class="meta">From {{ origin_name }} toward {{ destination_name }}</p>
      <section class="list">
        {% for dep in departures %}
          <article class="item">
            <div class="time">{{ dep.time }}</div>
            <div class="dir">{{ dep.direction }}</div>
            <div class="platform">Platform {{ dep.platform }}</div>
          </article>
        {% endfor %}
      </section>
    {% endif %}
  </main>
</body>
</html>
"""


def _resolve_location(api: VasttrafikAPI, query: str) -> Location:
    locations = api.get_locations(query=query, location_type="stoparea", limit=5)
    if not locations:
        raise ValueError(f"No stop area found for '{query}'.")

    exact_match = next((loc for loc in locations if loc.name.casefold() == query.casefold()), None)
    return exact_match or locations[0]


def _format_time(value: datetime) -> str:
    return value.astimezone().strftime("%H:%M")


def _default_date_time() -> tuple[str, str]:
    now = datetime.now().astimezone()
    return now.strftime("%Y-%m-%d"), now.strftime("%H:%M")


def _parse_selected_datetime(date_value: str, time_value: str) -> datetime:
    if not date_value:
        raise ValueError("Date is required.")

    selected_time = time_value or "00:00"
    combined = datetime.fromisoformat(f"{date_value}T{selected_time}")
    tzinfo = datetime.now().astimezone().tzinfo
    return combined.replace(tzinfo=tzinfo)


def create_app() -> Flask:
    app = Flask(__name__)

    @app.route("/", methods=["GET", "POST"])
    def index() -> str:
        default_date, default_time = _default_date_time()
        active_tab = request.args.get("tab", "search")
        if request.method == "POST":
            active_tab = request.form.get("tab", active_tab)

        origin = "Kapellplatsen"
        destination = "Järntorget"
        count = 5
        minutes = 90
        date_value = default_date
        time_value = default_time
        departures: List[Dict[str, Any]] = []
        error: Optional[str] = None
        fallback_used = False
        searched = False
        origin_name = ""
        destination_name = ""

        if request.method == "POST":
            searched = True
            if active_tab == "search":
                origin = request.form.get("origin", origin).strip()
                destination = request.form.get("destination", destination).strip()
            date_value = request.form.get("date", date_value).strip()
            time_value = request.form.get("time", time_value).strip()

            try:
                count = int(request.form.get("count", count))
                minutes = int(request.form.get("minutes", minutes))
                count = max(1, min(count, 20))
                minutes = max(1, min(minutes, 180))
            except ValueError:
                error = "Count and minutes must be numeric values."

        if active_tab == "next" and request.method == "GET":
            searched = True

        should_fetch = searched and not error
        if should_fetch:
            try:
                selected_datetime = _parse_selected_datetime(date_value, time_value)

                api = VasttrafikAPI()
                origin_location = _resolve_location(api, origin)
                destination_location = _resolve_location(api, destination)
                origin_name = origin_location.name
                destination_name = destination_location.name

                upcoming = api.get_departures(
                    origin_gid=origin_location.gid,
                    direction_gid=destination_location.gid,
                    limit=20,
                    minutes=minutes,
                    start_datetime=selected_datetime,
                )

                if not upcoming:
                    upcoming = api.get_departures(
                        origin_gid=origin_location.gid,
                        limit=20,
                        minutes=minutes,
                        start_datetime=selected_datetime,
                    )
                    fallback_used = True

                for departure in upcoming[:count]:
                    best_time = departure.estimated_time or departure.planned_time
                    departures.append(
                        {
                            "time": _format_time(best_time),
                            "direction": departure.direction or destination_location.name,
                            "platform": departure.platform or "-",
                        }
                    )
            except Exception as exc:
                error = str(exc)

        return render_template_string(
            PAGE_TEMPLATE,
            active_tab=active_tab,
            origin=origin,
            destination=destination,
            count=count,
            minutes=minutes,
            date=date_value,
            time=time_value,
            departures=departures,
            error=error,
            fallback_used=fallback_used,
            searched=searched,
            origin_name=origin_name,
            destination_name=destination_name,
        )

    return app


def main() -> None:
    app = create_app()
    app.run(host="127.0.0.1", port=8000, debug=False)
