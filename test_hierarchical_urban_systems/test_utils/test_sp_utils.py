import numpy as np
import scipy.sparse as sp  # type: ignore[import-untyped]

from hierarchical_urban_systems.utils.sp_utils import filter_small_values_from_matrix


def test_it_filters_small_values_from_sparse_matrix() -> None:
    matrix = np.array(
        [
            [
                1,
                0.59,
                4.5,
                13,
            ],
            [
                0.7,
                0,
                4,
                0.5,
            ],
            [
                0,
                0,
                20,
                17.5,
            ],
            [
                0.6,
                0.4,
                0,
                9,
            ],
        ],
        dtype=np.float32,
    )
    matrix_sp = sp.csr_matrix(matrix)

    filter_small_values_from_matrix(matrix=matrix_sp, min_value_threshold=0.6)

    expected_matrix = np.array(
        [
            [
                1,
                0,
                4.5,
                13,
            ],
            [
                0.7,
                0,
                4,
                0,
            ],
            [
                0,
                0,
                20,
                17.5,
            ],
            [
                0.6,
                0,
                0,
                9,
            ],
        ],
        dtype=np.float32,
    )

    assert np.allclose(expected_matrix, matrix_sp.todense())
