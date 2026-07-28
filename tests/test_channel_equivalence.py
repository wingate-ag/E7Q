# SPDX-License-Identifier: Apache-2.0
import pytest

from e7q.cli import main
from e7q.language import E7QError, compare, comparison_result, parse


def _channel(name: str, operations: str):
    return parse(f"""
context {name} {{
  backend: densitymatrix
  shots: 128
}}
qubits q[1]
bits c[1]
path Channel {{
{operations}
  measure q -> c
}}
verify Channel
""")


def test_identical_noise_channels_are_exactly_equivalent():
    first = _channel("First", "  noise bit_flip(0.2) q[0]")
    second = _channel("Second", "  noise bit_flip(0.2) q[0]")
    result = comparison_result(compare(first, second, "channel-exact"))
    assert result["status"] == "PASS"
    assert result["maximum_error"] == 0
    assert result["proof"][0]["representation"] == "superoperator"


def test_channel_tolerance_detects_probability_difference():
    first = _channel("First", "  noise bit_flip(0.2) q[0]")
    close = _channel("Close", "  noise bit_flip(0.200001) q[0]")
    assert compare(first, close, "channel-tolerance", 1e-5).equivalent
    assert not compare(first, close, "channel-tolerance", 1e-7).equivalent


def test_measurement_channel_equivalence_is_weaker():
    identity = _channel("Identity", "")
    phase_flip = _channel("PhaseFlip", "  noise phase_flip(1.0) q[0]")
    assert not compare(identity, phase_flip, "channel-exact").equivalent
    assert compare(identity, phase_flip, "channel-measurement").equivalent


def test_channel_comparison_rejects_statevector():
    density = _channel("Density", "")
    statevector = parse("""
context Statevector { backend: statevector }
qubits q[1]
bits c[1]
path Circuit { measure q -> c }
verify Circuit
""")
    with pytest.raises(E7QError, match="densitymatrix"):
        compare(density, statevector, "channel-exact")


def test_channel_compare_cli(tmp_path):
    first = tmp_path / "first.e7q"
    second = tmp_path / "second.e7q"
    source = """
context Noise { backend: densitymatrix }
qubits q[1]
bits c[1]
path Channel {
  noise depolarizing(0.1) q[0]
  measure q -> c
}
verify Channel
"""
    first.write_text(source)
    second.write_text(source)
    proof = tmp_path / "channel.proof.json"
    assert main([
        "compare", str(first), str(second),
        "--criterion", "channel-exact", "--proof", str(proof),
    ]) == 0
    assert '"representation": "superoperator"' in proof.read_text()
