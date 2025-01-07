import numpy as np
import pytest
import scipy.sparse as sp  # type: ignore[import-untyped]


@pytest.fixture
def flows_matrix() -> sp.csr_matrix:
    flows_data = np.array(
        [[25, 10, 0, 0], [10, 0, 10, 10], [0, 10, 10, 20], [0, 10, 20, 30]],
        dtype=np.float32,
    )
    return sp.csr_matrix(flows_data)


@pytest.fixture()
def node_sizes(flows_matrix: sp.csr_matrix) -> np.ndarray:
    return flows_matrix.sum(axis=1).A[:, 0]
