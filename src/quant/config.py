import os
import yaml
from dotenv import load_dotenv

load_dotenv()

def load_cfg(path: str = "config.yaml") -> dict:
    with open(path) as f:
        return yaml.safe_load(f)