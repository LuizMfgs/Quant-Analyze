"""Command-line entry point: `forecast-portfolio run [--refresh] [--config PATH]`."""

from __future__ import annotations

import argparse
import logging

from .config import Settings
from .pipeline import run


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="forecast-portfolio",
        description="Prophet forecasting + Markowitz portfolio optimisation",
    )
    parser.add_argument("command", choices=["run"], help="run the full pipeline")
    parser.add_argument("--config", default=None, help="path to settings.yaml")
    parser.add_argument("--refresh", action="store_true",
                        help="ignore the CSV cache and download fresh data")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    settings = Settings.from_yaml(args.config)
    run(settings, refresh=args.refresh)
    print("Done — see outputs/results.json")


if __name__ == "__main__":
    main()
