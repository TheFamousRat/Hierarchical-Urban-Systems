import scipy.sparse as sp  # type: ignore[import-untyped]


def filter_small_values_from_matrix(
    matrix: sp.spmatrix, min_value_threshold: float
) -> sp.spmatrix:
    matrix.data[matrix.data < min_value_threshold] = 0.0
    matrix.eliminate_zeros()
    return matrix
