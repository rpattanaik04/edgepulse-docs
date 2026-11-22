"""Check that every code sample in the guides is identical to the tested file in examples/.

The guides show full code listings. This script prevents the documentation and the
tested code from drifting apart. Run it from the repository root:

    python scripts/check_examples_in_docs.py

It exits with a non-zero status if a listing is missing or has changed.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Example file -> the guide that must contain it, word for word.
LISTINGS = {
    "examples/python/edgepulse_client.py": "docs/developer-guide/index.md",
    "examples/python/list_problem_devices.py": "docs/developer-guide/index.md",
    "examples/python/simulate_device.py": "docs/developer-guide/index.md",
    "examples/python/mqtt_bridge.py": "docs/integration/mqtt.md",
    "examples/node/list_devices.mjs": "docs/developer-guide/index.md",
    "examples/python/get_token.py": "docs/api/authentication.md",
    "examples/node/get_token.mjs": "docs/api/authentication.md",
}

failures = 0
for example, guide in LISTINGS.items():
    code = (ROOT / example).read_text(encoding="utf-8").strip()
    text = (ROOT / guide).read_text(encoding="utf-8")
    if code in text:
        print(f"ok    {example}  ->  {guide}")
    else:
        print(f"FAIL  {example} does not match its listing in {guide}")
        failures += 1

sys.exit(1 if failures else 0)
