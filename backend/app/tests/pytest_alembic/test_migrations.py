import logging
import warnings

import pytest as pytest
from pytest_alembic import tests
from pytest_alembic.plugin.error import AlembicTestFailure
from pytest_alembic.runner import MigrationContext

logger = logging.getLogger(__name__)


@pytest.mark.alembic
def test_single_head_revision(alembic_runner: MigrationContext) -> None:
    tests.test_single_head_revision(alembic_runner)


@pytest.mark.alembic
def test_upgrade(alembic_runner: MigrationContext) -> None:
    tests.test_upgrade(alembic_runner)


@pytest.mark.alembic
def test_model_definitions_match_ddl(alembic_runner: MigrationContext) -> None:
    tests.test_model_definitions_match_ddl(alembic_runner)


NOT_IMPLEMENTED_WARNING = (
    "The {revision} downgrade raised `NotImplementedError`, "
    "which short-circuited the downgrade "
    "operation and may have passed the test. "
    "If intended, and downgrades can not safely be performed "
    "below this migration, "
    "see 'minimum_downgrade_revision' configuration to avoid this warning."
)


@pytest.mark.alembic
def test_up_down_consistency(alembic_runner: MigrationContext) -> None:
    # Skip the `heads` revision. Caused by new alembic warning in 1.6.x.
    down_revisions = list(reversed(alembic_runner.history.revisions[:-1]))

    index = 0
    for index, revision in enumerate(down_revisions):
        if alembic_runner.config.minimum_downgrade_revision == revision:
            # If there is a minimum_downgrade_revision, stop downgrading here.
            break
        elif revision == "base":
            continue
        try:
            alembic_runner.migrate_down_to(revision)
        except NotImplementedError:
            # In the event of a `NotImplementedError`,
            # we should have the same semantics,
            # as-if `minimum_downgrade_revision` was specified,
            # but we'll emit a warning
            # to suggest that feature is used instead.
            warnings.warn(NOT_IMPLEMENTED_WARNING.format(revision=revision))
            break

        except Exception as e:
            raise AlembicTestFailure(
                "Failed to downgrade through each revision individually.",
                context=[("Failing Revision", revision), ("Alembic Error", str(e))],
            )

    # We should only upgrade as far as we successfully downgraded.
    down_revisions = down_revisions[:index]

    for revision in reversed(down_revisions):
        try:
            alembic_runner.migrate_up_to(revision)
        except Exception as e:
            raise AlembicTestFailure(
                (
                    "Failed to upgrade through each revision "
                    "individually after performing a "
                    "roundtrip upgrade -> downgrade -> upgrade cycle."
                ),
                context=[("Failing Revision", revision), ("Alembic Error", str(e))],
            )
