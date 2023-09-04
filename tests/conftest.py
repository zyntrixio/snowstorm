import pytest


def pytest_addoption(parser):
    parser.addoption("--days", action="store", type=int, default=35, help="days to keep")
    parser.addoption("--events", action="store", type=int, default=10, help="no.of events")


@pytest.fixture(scope="session")
def days(pytestconfig):
    """Returns no.of days"""
    return pytestconfig.getoption("days")


@pytest.fixture(scope="session")
def test_event_count(pytestconfig):
    """Returns no.of events"""
    return pytestconfig.getoption("events")
