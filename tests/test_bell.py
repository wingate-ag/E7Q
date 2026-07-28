# SPDX-License-Identifier: Apache-2.0
import numpy as np

from e7q.reference import bell_state, is_normalized, probabilities


def test_bell_state_invariants():
    state = bell_state()
    assert is_normalized(state)
    assert np.allclose(probabilities(state), [0.5, 0.0, 0.0, 0.5])
