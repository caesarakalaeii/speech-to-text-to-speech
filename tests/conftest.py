import pytest

from stts import models


@pytest.fixture(scope="session")
def models_ready():
    """Skip unless the ONNX models are on disk.

    These are ~870 MB, so we never download them implicitly from a test run.
    Get them with `uv run stts setup`.
    """
    if not models.all_ready():
        pytest.skip("models not downloaded — run `uv run stts setup`")
    return True


@pytest.fixture(scope="session")
def synthesiser(models_ready):
    from stts.tts import Synthesiser

    synth = Synthesiser(use_gpu=False)
    synth.warm_up()
    return synth


@pytest.fixture(scope="session")
def recogniser(models_ready):
    from stts.stt import Recogniser

    return Recogniser(use_gpu=False)


@pytest.fixture(scope="session")
def vad(models_ready):
    from stts.vad import SileroVad

    return SileroVad(models.download_vad())
