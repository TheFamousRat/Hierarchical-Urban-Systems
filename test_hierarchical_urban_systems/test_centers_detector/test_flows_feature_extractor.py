import numpy as np
import scipy.sparse as sp  # type: ignore[import-untyped]
from sklearn.preprocessing import normalize  # type: ignore[import-untyped]

from hierarchical_urban_systems.centers_detector.flows_feature_extractor import (
    FlowsFeatureExtractor,
    DistanceType,
)


def test_it_computes_inv_dist_mat_as_expected_with_geometric_distance(
    flows_matrix: sp.csr_matrix, node_sizes: np.ndarray
) -> None:
    sparse_result = FlowsFeatureExtractor.build_inverse_distances_matrix(
        flows_matrix=flows_matrix,
        node_sizes=node_sizes,
        distance_type=DistanceType.GEOMETRIC_MEAN,
    )
    dense_result = FlowsFeatureExtractor.build_inverse_distances_matrix(
        flows_matrix=flows_matrix.todense().A,
        node_sizes=node_sizes,
        distance_type=DistanceType.GEOMETRIC_MEAN,
    )

    assert isinstance(sparse_result, sp.csr_matrix)
    assert isinstance(dense_result, np.ndarray)

    assert sparse_result.nnz == 11
    assert sparse_result.shape == (4, 4)
    assert dense_result.shape == (4, 4)

    assert np.allclose(sparse_result.todense(), dense_result)

    for row in range(4):
        for col in range(4):
            assert np.isclose(
                sparse_result[row, col],
                flows_matrix[row, col] / np.sqrt(node_sizes[row] * node_sizes[col]),
            )
            assert np.isclose(
                dense_result[row, col],
                flows_matrix[row, col] / np.sqrt(node_sizes[row] * node_sizes[col]),
            )


def test_it_computes_inv_dist_mat_as_expected_with_arithmetic_distance(
    flows_matrix: sp.csr_matrix, node_sizes: np.ndarray
) -> None:
    sparse_result = FlowsFeatureExtractor.build_inverse_distances_matrix(
        flows_matrix=flows_matrix,
        node_sizes=node_sizes,
        distance_type=DistanceType.ARITHMETIC_MEAN,
    )
    dense_result = FlowsFeatureExtractor.build_inverse_distances_matrix(
        flows_matrix=flows_matrix.todense().A,
        node_sizes=node_sizes,
        distance_type=DistanceType.ARITHMETIC_MEAN,
    )

    assert isinstance(sparse_result, sp.csr_matrix)
    assert isinstance(dense_result, np.ndarray)

    assert sparse_result.nnz == 11
    assert sparse_result.shape == (4, 4)
    assert dense_result.shape == (4, 4)

    assert np.allclose(sparse_result.todense(), dense_result)

    for row in range(4):
        for col in range(4):
            assert np.isclose(
                sparse_result[row, col],
                2.0 * flows_matrix[row, col] / (node_sizes[row] + node_sizes[col]),
            )
            assert np.isclose(
                dense_result[row, col],
                2.0 * flows_matrix[row, col] / (node_sizes[row] + node_sizes[col]),
            )


def test_it_computes_indirect_flows_properly(flows_matrix: sp.csr_matrix) -> None:
    indirect_flows_0 = FlowsFeatureExtractor.get_indirect_flows_matrix(
        direct_flows_matrix=flows_matrix, degree=0
    )
    assert isinstance(indirect_flows_0, sp.csr_matrix)
    assert np.allclose(flows_matrix.todense().A, indirect_flows_0.todense().A)

    expected_indirect_flows = flows_matrix.todense().A
    expected_indirect_flows = expected_indirect_flows @ normalize(
        expected_indirect_flows, axis=1, norm="l1"
    )
    expected_indirect_flows = expected_indirect_flows @ normalize(
        expected_indirect_flows, axis=1, norm="l1"
    )

    indirect_flows_2 = FlowsFeatureExtractor.get_indirect_flows_matrix(
        direct_flows_matrix=flows_matrix, degree=2
    )
    assert isinstance(indirect_flows_2, sp.csr_matrix)
    assert np.allclose(expected_indirect_flows, indirect_flows_2.todense().A)


def test_it_keeps_flows_properties_in_indirect_flows(
    flows_matrix: sp.csr_matrix,
) -> None:
    node_sizes = flows_matrix.sum(axis=1).A[:, 0]

    for degree in range(5):
        indirect_flows = FlowsFeatureExtractor.get_indirect_flows_matrix(
            direct_flows_matrix=flows_matrix, degree=degree
        )
        assert np.allclose(indirect_flows.sum(axis=1).A[:, 0], node_sizes)
