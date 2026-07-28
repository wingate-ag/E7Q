# SPDX-License-Identifier: Apache-2.0
from pathlib import Path

import pytest

from e7q.language import E7QError, backend_profile, load, parse, run, verify


EXAMPLES = Path(__file__).parents[1] / "examples"


def test_noisy_bell_uses_density_matrix_and_preserves_trace():
    program = load(EXAMPLES / "noisy-bell.e7q")
    result = verify(run(program))
    assert result["status"] == "PASS"
    assert result["evidence"]["trace"] == pytest.approx(1.0)
    assert result["evidence"]["purity"] == pytest.approx(0.82)
    assert result["evidence"]["channels"] == 1
    assert set(result["probabilities"]) == {"00", "01", "10", "11"}
    assert result["probabilities"]["00"] == pytest.approx(0.45)
    assert result["probabilities"]["11"] == pytest.approx(0.45)
    assert result["probabilities"]["01"] == pytest.approx(0.05)
    assert result["probabilities"]["10"] == pytest.approx(0.05)


@pytest.mark.parametrize("channel", ["bit_flip", "phase_flip", "depolarizing"])
def test_supported_channels_are_trace_preserving(channel):
    source = (EXAMPLES / "noisy-bell.e7q").read_text()
    program = parse(source.replace("bit_flip(0.10)", f"{channel}(0.10)"))
    result = verify(run(program))
    assert result["status"] == "PASS"
    assert result["evidence"]["trace"] == pytest.approx(1.0)


def test_noise_requires_densitymatrix_backend():
    source = (EXAMPLES / "noisy-bell.e7q").read_text()
    with pytest.raises(E7QError, match="densitymatrix"):
        parse(source.replace("backend: densitymatrix", "backend: statevector"))


def test_backend_profile_declares_requirements_and_boundary():
    profile = backend_profile(load(EXAMPLES / "noisy-bell.e7q"))
    assert profile["requires"]["density_matrix"]
    assert profile["requires"]["noise_channels"] == ["bit_flip"]
    assert "no physical hardware fidelity" in profile["boundary"]
