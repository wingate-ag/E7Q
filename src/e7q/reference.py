# SPDX-License-Identifier: Apache-2.0
"""Minimal E7Q state-vector reference primitives (pre-alpha)."""
from __future__ import annotations

import numpy as np

H = np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2)
X = np.array([[0, 1], [1, 0]], dtype=complex)
CX = np.array(
    [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]],
    dtype=complex,
)


def zero_state(qubits: int) -> np.ndarray:
    if qubits < 1:
        raise ValueError("qubits must be positive")
    state = np.zeros(2**qubits, dtype=complex)
    state[0] = 1.0
    return state


def apply_single(state: np.ndarray, gate: np.ndarray, target: int, qubits: int) -> np.ndarray:
    if not 0 <= target < qubits:
        raise IndexError("target qubit out of range")
    operator = np.array([[1.0 + 0j]])
    for index in range(qubits):
        operator = np.kron(operator, gate if index == target else np.eye(2))
    return operator @ state


def bell_state() -> np.ndarray:
    state = apply_single(zero_state(2), H, target=0, qubits=2)
    return CX @ state


def probabilities(state: np.ndarray) -> np.ndarray:
    return np.abs(state) ** 2


def is_normalized(state: np.ndarray, tolerance: float = 1e-12) -> bool:
    return bool(np.isclose(np.vdot(state, state).real, 1.0, atol=tolerance))
