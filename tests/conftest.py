"""Configuration for the pytest test suite."""

from copy import deepcopy
from pathlib import Path

import dir_content_diff
import dir_content_diff.comparators.pandas
import luigi
import pytest
import requests
import urllib3
from luigi_tools.task import WorkflowTask

DATA = Path(__file__).parent / "data"
EXAMPLES = Path(__file__).parent.parent / "examples"
EXAMPLES_TEST = Path(__file__).parent / "examples_test"

dir_content_diff.comparators.pandas.register()


def _external_service_available(url):
    """Return whether an external HTTP service responds successfully."""
    try:
        urllib3.disable_warnings()
        response = requests.get(url, timeout=10, verify=False)
    except requests.RequestException:
        return False
    return response.ok


@pytest.fixture
def _require_neuromorpho_api():
    """Skip tests when the NeuroMorpho API is unavailable."""
    if not _external_service_available("http://cng.gmu.edu:8080/api/health"):
        pytest.skip("NeuroMorpho API is unavailable")


@pytest.fixture
def _require_mouselight_api():
    """Skip tests when external APIs required by MouseLight downloads are unavailable."""
    if not _external_service_available("https://ml-neuronbrowser.janelia.org/api/v1/neurons"):
        pytest.skip("MouseLight API is unavailable")
    if not _external_service_available("http://cng.gmu.edu:8080/api/health"):
        pytest.skip("NeuroMorpho API is unavailable (required by morphapi)")


@pytest.fixture
def tmp_working_dir(tmp_path, monkeypatch):
    """Change working directory before a test and change it back when the test is finished."""
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.fixture
def data_dir():
    """The data directory."""
    return DATA


@pytest.fixture
def examples_dir():
    """The examples directory."""
    return EXAMPLES


@pytest.fixture
def examples_test_dir():
    """The examples directory."""
    return EXAMPLES_TEST


@pytest.fixture
def WorkflowTask_exception_event():
    """Fixture to catch exception from tasks deriving from WorkflowTask.

    The events of the tasks are reset afterwards.
    """
    # pylint: disable=protected-access
    current_callbacks = deepcopy(luigi.Task._event_callbacks)  # noqa: SLF001

    failed_task = []
    exceptions = []

    @WorkflowTask.event_handler(luigi.Event.FAILURE)
    def check_exception(task, exception):
        failed_task.append(str(task))
        exceptions.append(str(exception))

    yield failed_task, exceptions

    luigi.Task._event_callbacks = current_callbacks  # noqa: SLF001
