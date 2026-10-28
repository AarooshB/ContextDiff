import json
from pathlib import Path

import pytest

from contextdiff import load_json_snapshot

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def status_pair():
    return (
        load_json_snapshot((FIXTURES / "statuses.before.json").read_bytes()),
        load_json_snapshot((FIXTURES / "statuses.after.json").read_bytes()),
    )


@pytest.fixture
def expected_statuses():
    return json.loads((FIXTURES / "statuses.expected.json").read_text())
