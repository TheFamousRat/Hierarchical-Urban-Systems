import logging
from enum import Enum
from typing import Literal

import numpy as np
import scipy.sparse as sp  # type: ignore[import-untyped]
from sklearn.preprocessing import normalize  # type: ignore[import-untyped]
import tqdm  # type: ignore[import-untyped]

from hierarchical_urban_systems.alias import FlowMatrix
from hierarchical_urban_systems.constants import TQDM_COLS_COUNT

_logger = logging.getLogger(name=__name__)
logging.basicConfig(level=logging.INFO)


class DistanceType(Enum):
    GEOMETRIC_MEAN = "GEOMETRIC_MEAN"
    ARITHMETIC_MEAN = "ARITHMETIC_MEAN"


class FlowsFeatureExtractor:
    @classmethod
    def build_similarity_matrix_from_flows(
        cls, flows_matrix: FlowMatrix, norm: Literal["l1", "l2", "max"] = "l2"
    ) -> sp.csr_matrix:
        _logger.debug(
            f"Computing similarity matrix between {flows_matrix.shape[0]} nodes."
        )
        features_matrix = normalize(flows_matrix, axis=1, norm=norm)
        similarity_matrix: sp.csr_matrix = features_matrix @ features_matrix.T

        if isinstance(similarity_matrix, sp.spmatrix):
            similarity_matrix.eliminate_zeros()

        return similarity_matrix

    @classmethod
    def get_local_flows_matrix(
        cls,
        flows_matrix: sp.spmatrix,
        node_sizes: np.ndarray,
        distance_type: DistanceType,
    ) -> sp.spmatrix:
        inv_dist_mat = cls.build_inverse_distances_matrix(
            flows_matrix=flows_matrix,
            node_sizes=node_sizes,
            distance_type=distance_type,
        )
        local_flows_matrix = flows_matrix.multiply(inv_dist_mat)
        return local_flows_matrix

    @classmethod
    def build_inverse_distances_matrix(
        cls,
        flows_matrix: FlowMatrix,
        node_sizes: np.ndarray,
        distance_type: DistanceType,
    ) -> sp.spmatrix:
        assert flows_matrix.shape[0] == len(node_sizes)

        rows, cols = flows_matrix.nonzero()

        if distance_type == DistanceType.GEOMETRIC_MEAN:
            sqrt_node_sizes = np.sqrt(node_sizes)
            inv_sqrt_node_sizes = np.reciprocal(sqrt_node_sizes)

            normalization_matrix = sp.csr_matrix(
                (
                    inv_sqrt_node_sizes[rows] * inv_sqrt_node_sizes[cols],
                    (rows, cols),
                ),
                dtype=np.float32,
                shape=flows_matrix.shape,
            )

            inv_dist_mat = normalization_matrix.multiply(flows_matrix)
        elif distance_type == DistanceType.ARITHMETIC_MEAN:
            normalization_matrix = sp.csr_matrix(
                (
                    2.0 / (node_sizes[rows] + node_sizes[cols]),
                    (rows, cols),
                ),
                dtype=np.float32,
                shape=flows_matrix.shape,
            )

            inv_dist_mat = normalization_matrix.multiply(flows_matrix)
        else:
            raise ValueError(f"Unknown distance type: '{distance_type}'")

        if isinstance(flows_matrix, np.ndarray):
            inv_dist_mat = inv_dist_mat.todense().A

        return inv_dist_mat

    @staticmethod
    def get_indirect_flows_matrix(
        direct_flows_matrix: sp.csr_matrix,
        degree: int = 1,
        min_value_threshold: float = 0.1,
    ) -> sp.csr_matrix:
        if degree < 0:
            raise ValueError(
                f"Indirect flows make sense only for positive degrees (got {degree})."
            )

        if degree == 0:
            _logger.debug(
                "Indirect flows of degree 0 correspond to the flows themselves."
                " Returning them."
            )
            return direct_flows_matrix

        _logger.debug(
            f"Computing the indirect flows for {len(direct_flows_matrix.data)} flows."
        )
        node_sizes = direct_flows_matrix.sum(axis=1).A
        flows_proportion = normalize(direct_flows_matrix.todense().A, axis=1, norm="l1")
        for _degree in tqdm.tqdm(
            range(degree), desc="Flows degree reached", ncols=TQDM_COLS_COUNT
        ):
            flows_proportion = flows_proportion @ flows_proportion

        indirect_flows = flows_proportion * node_sizes
        indirect_flows = sp.csr_matrix(
            indirect_flows * (indirect_flows >= min_value_threshold)
        )

        return indirect_flows
