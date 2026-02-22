from datetime import datetime
from typing import Optional

import click

from kapell.api import Location, VasttrafikAPI


def _resolve_location(api: VasttrafikAPI, query: str) -> Location:
    locations = api.get_locations(query=query, location_type="stoparea", limit=5)
    if not locations:
        raise click.ClickException(f"No stop area found for '{query}'.")

    exact_match = next((loc for loc in locations if loc.name.casefold() == query.casefold()), None)
    return exact_match or locations[0]


def _format_time(value: datetime) -> str:
    return value.astimezone().strftime("%H:%M")


def _pick_location_value(
    arg_value: Optional[str],
    flag_value: Optional[str],
    label: str,
) -> str:
    value = flag_value or arg_value
    if not value:
        raise click.ClickException(
            f"Missing {label}. Use positional arguments or --{label}."
        )
    return value


@click.group()
def cli() -> None:
    """Kapell CLI for Västtrafik departures."""


@cli.command("next")
@click.argument("origin_arg", required=False)
@click.argument("destination_arg", required=False)
@click.option("--origin", "origin_opt", help="Origin stop area name.")
@click.option("--destination", "destination_opt", help="Destination stop area name.")
@click.option("--count", default=3, show_default=True, type=click.IntRange(1, 20))
@click.option("--minutes", default=60, show_default=True, type=click.IntRange(1, 180))
def next_command(
    origin_arg: Optional[str],
    destination_arg: Optional[str],
    origin_opt: Optional[str],
    destination_opt: Optional[str],
    count: int,
    minutes: int,
) -> None:
    """Show upcoming line 61 departures from ORIGIN toward DESTINATION."""
    fallback_used = False

    try:
        origin = _pick_location_value(origin_arg, origin_opt, "origin")
        destination = _pick_location_value(destination_arg, destination_opt, "destination")

        api = VasttrafikAPI()
        origin_location = _resolve_location(api, origin)
        destination_location = _resolve_location(api, destination)

        departures = api.get_departures(
            origin_gid=origin_location.gid,
            direction_gid=destination_location.gid,
            limit=20,
            minutes=minutes,
        )

        if not departures:
            departures = api.get_departures(
                origin_gid=origin_location.gid,
                limit=20,
                minutes=minutes,
            )
            fallback_used = True
    except Exception as exc:
        raise click.ClickException(str(exc)) from exc

    if not departures:
        click.echo(
            f"No line 61 departures from {origin_location.name} toward "
            f"{destination_location.name} in the next {minutes} minutes."
        )
        return

    click.echo(
        f"Next line 61 departures from {origin_location.name} "
        f"toward {destination_location.name}:"
    )
    if fallback_used:
        click.echo(
            "No departures matched destination as terminal stop; "
            "showing all line 61 departures from origin."
        )

    for departure in departures[:count]:
        best_time = departure.estimated_time or departure.planned_time
        time_text = _format_time(best_time)
        platform = departure.platform or "-"
        click.echo(f"{time_text}  to {departure.direction or destination_location.name}  platform {platform}")


@cli.command("web")
@click.option("--host", default="127.0.0.1", show_default=True)
@click.option("--port", default=8000, show_default=True, type=click.IntRange(1, 65535))
@click.option("--debug", is_flag=True, help="Enable Flask debug mode.")
def web_command(host: str, port: int, debug: bool) -> None:
    """Run the Kapell web GUI."""
    from kapell.web import create_app

    app = create_app()
    click.echo(f"Starting Kapell web GUI at http://{host}:{port}")
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    cli()

