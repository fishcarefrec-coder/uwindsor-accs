import pytest

from app.config import settings
from app.core.limiter import limiter


@pytest.fixture(autouse=True, scope="session")
def disable_rate_limiting():
    """Turn the request limiter off for the whole test session.

    RATE_LIMIT_LOGIN is 5/minute keyed on client IP, and every test runs from
    the same address. Any test that logs in therefore eats into the budget of
    whichever tests run after it, so a suite that passes on its own starts
    failing once another login-heavy test is added — failures that track
    execution order rather than the code under test.

    The limiter itself is still worth exercising, but that belongs in a test
    written for it specifically, not as a side effect on everything else.
    """
    limiter.enabled = False
    yield
    limiter.enabled = True


@pytest.fixture(autouse=True, scope="session")
def known_superadmin_password():
    """Give the first-boot super admin a fixed password for the test session.

    Production leaves SUPERADMIN_PASSWORD unset and gets a random one; the
    acceptance tests log in as the seeded account, so they need to know it.
    """
    settings.SUPERADMIN_PASSWORD = "ChangeMe123!"
    yield
