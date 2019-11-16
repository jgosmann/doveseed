from datetime import datetime, timedelta
import json

from tinydb import TinyDB

from doveseed.storage import TinyDbStorage


def clean_unconfirmed(config_filename: str) -> None:
    with open(config_filename, "r") as f:
        config = json.load(f)
    db = TinyDB(config["db"])
    storage = TinyDbStorage(db)
    storage.drop_old_unconfirmed(
        drop_before=datetime.utcnow()
        - timedelta(minutes=config["confirm_timeout_minutes"])
    )


if __name__ == "__main__":
    import argparse
    import os
    import os.path

    parser = argparse.ArgumentParser(
        description="Cleans outdated pending subscriptions."
    )
    parser.add_argument(
        "config", type=str, nargs=1, help="configuration file", metavar="config"
    )

    args = parser.parse_args()

    os.chdir(os.path.dirname(os.path.abspath(args.config[0])))
    clean_unconfirmed(args.config[0])
