import logging
from typing import Generator

import numpy as np
import scipy.sparse as sp  # type: ignore[import-untyped]

from hierarchical_urban_systems.alias import FlowMatrix
from hierarchical_urban_systems.centers_detector.flows_feature_extractor import (
    FlowsFeatureExtractor,
    DistanceType,
)
from hierarchical_urban_systems.constants import NO_CENTER_IDX
from hierarchical_urban_systems.utils.sp_utils import filter_small_values_from_matrix

_logger = logging.getLogger(name=__name__)


class CenterDetector:
    def __init__(
        self,
        flows_matrix: sp.csr_matrix,
    ) -> None:
        self.flows_matrix = flows_matrix

        self.nodes_count = self.flows_matrix.shape[0]
        self.node_sizes = self.flows_matrix.sum(axis=1).A[:, 0]

        # TODO: It's not super intuitive that the "first" level of the assignment is every node to itself.
        # Maybe level "0" should really be level "1", with the mapping of every node to itself not stored here
        self._leveled_centers_assignment = np.arange(self.nodes_count, dtype=np.int32)[
            None, :
        ]

    def iterate_computed_assignments(
        self, start_level: int = 0
    ) -> Generator[np.ndarray, None, None]:
        for level in range(start_level, self._leveled_centers_assignment.shape[0]):
            yield self._leveled_centers_assignment[level, :]

    def get_assignment_of_level(self, level: int) -> np.ndarray:
        return self.get_leveled_assignments(min_level=level, max_level=level)[0, :]

    def get_leveled_assignments(self, min_level: int, max_level: int) -> np.ndarray:
        if min(min_level, max_level) < 0:
            raise ValueError(
                f"Center levels must be at least zero, got ({min_level},{max_level})"
            )

        while max_level > self._leveled_centers_assignment.shape[0] - 1:
            current_max_degree = self._leveled_centers_assignment.shape[0] - 1

            _logger.info(f"Computing assignment of level {current_max_degree+1}")
            # assignment_this_degree = self._compute_next_assignment_level()
            assignment_this_degree = self._compute_assignment_of_level(
                initial_assignment_level=current_max_degree,
                target_assignment_level=current_max_degree + 1,
            )
            self._leveled_centers_assignment = np.vstack(
                (self._leveled_centers_assignment, assignment_this_degree),
                dtype=np.int32,
            )

        return self._leveled_centers_assignment[min_level : max_level + 1, :]

    @classmethod
    def get_center_flows_of_degree(
        cls,
        flows_matrix: sp.spmatrix,
        centers_assignment: np.ndarray,
        flows_degree: int = 0,
    ) -> sp.csr_matrix:
        center_flows = cls._get_centers_flow_matrix(
            flows_matrix=flows_matrix,
            centers_assignment=centers_assignment,
        )
        indirect_flows = FlowsFeatureExtractor.get_indirect_flows_matrix(
            direct_flows_matrix=center_flows, degree=flows_degree
        )
        return indirect_flows

    def get_inter_levels_assignment(
        self, start_level: int, end_level: int
    ) -> np.ndarray:
        if start_level == 0:
            return self.get_assignment_of_level(level=end_level)

        start_assignment = self.get_assignment_of_level(level=start_level)
        end_assignment = self.get_assignment_of_level(level=end_level)
        unique_center_node_idx = np.unique(start_assignment)

        node_to_center_idx_mapping = np.full_like(
            start_assignment, fill_value=len(start_assignment), dtype=np.int32
        )
        node_to_center_idx_mapping[unique_center_node_idx] = np.arange(
            len(unique_center_node_idx)
        )

        return node_to_center_idx_mapping[end_assignment[unique_center_node_idx]]

    def _compute_assignment_of_level(
        self, initial_assignment_level: int, target_assignment_level: int
    ) -> np.ndarray:
        assert initial_assignment_level <= target_assignment_level, (
            "Can not compute an assignment where the starting level is higher than the"
            " target one."
        )
        assert target_assignment_level >= 0, "Levels must be at least zero."

        initial_assignment = self._leveled_centers_assignment[
            initial_assignment_level, :
        ]

        center_sizes = np.bincount(
            initial_assignment,
            weights=self.node_sizes,
            minlength=self.nodes_count,
        )[np.unique(initial_assignment)]
        center_flows = self._get_centers_flow_matrix(
            flows_matrix=self.flows_matrix,
            centers_assignment=initial_assignment,
        )
        local_inv_dist_mat = FlowsFeatureExtractor.build_inverse_distances_matrix(
            flows_matrix=center_flows,
            node_sizes=center_sizes,
            distance_type=DistanceType.GEOMETRIC_MEAN,
        )
        center_flows = center_flows.multiply(local_inv_dist_mat)
        indirect_flows = FlowsFeatureExtractor.get_indirect_flows_matrix(
            direct_flows_matrix=center_flows,
            degree=target_assignment_level - 1,
            min_value_threshold=0.1,
        )

        _logger.info("Computing inter-nodes potentials matrix...")
        potentials = indirect_flows @ filter_small_values_from_matrix(
            FlowsFeatureExtractor.build_similarity_matrix_from_flows(
                local_inv_dist_mat
            ),
            1e-3,
        )

        target_level_assignment = self._get_assignment_from_affinity_matrix(
            affinity_matrix=potentials,
            centers_assignment=initial_assignment,
        )

        return target_level_assignment

    def _get_assignment_from_affinity_matrix(
        self, affinity_matrix: sp.spmatrix, centers_assignment: np.ndarray | None = None
    ) -> np.ndarray:
        if centers_assignment is None:
            centers_assignment = np.arange(self.nodes_count, dtype=np.int32)

        raw_intercenter_assignment = affinity_matrix.argmax(axis=1).A[:, 0]
        no_affinity_mask = np.where(
            affinity_matrix.max(axis=1).todense().A[:, 0] <= 0.0
        )[0]
        raw_intercenter_assignment[no_affinity_mask] = no_affinity_mask

        raw_supercenters_assignment = np.arange(self.nodes_count, dtype=np.int32)
        raw_supercenters_assignment[np.unique(centers_assignment)] = np.unique(
            centers_assignment
        )[raw_intercenter_assignment]
        raw_supercenters_assignment = raw_supercenters_assignment[centers_assignment]

        stabilized_assignment = self._stabilize_raw_assignment(
            raw_assignment=raw_supercenters_assignment,
        )

        largest_center_assignment = self._get_largest_node_assignment(
            assignment=stabilized_assignment, previous_assignment=centers_assignment
        )

        return largest_center_assignment

    def _get_largest_node_assignment(
        self, assignment: np.ndarray, previous_assignment: np.ndarray | None
    ) -> np.ndarray:
        if previous_assignment is None:
            previous_assignment = np.arange(self.nodes_count)

        center_sizes = np.bincount(
            previous_assignment, self.node_sizes, minlength=self.nodes_count
        )

        largest_node_assignment = assignment.copy()
        for center_idx in np.unique(assignment):
            center_nodes = np.where(assignment == center_idx)[0]
            largest_center_node_idx = center_nodes[center_sizes[center_nodes].argmax()]
            largest_node_assignment[center_nodes] = largest_center_node_idx

        return largest_node_assignment

    @classmethod
    def _get_rows_summings_matrix(cls, centers_assignment: np.ndarray) -> sp.csr_matrix:
        nodes_count = centers_assignment.size
        unique_center_nodes_idx = np.unique(centers_assignment)

        centers_count = unique_center_nodes_idx.size
        center_nodes_idx_mapping = np.zeros(nodes_count, dtype=np.int64)
        center_nodes_idx_mapping[unique_center_nodes_idx] = np.arange(centers_count)
        center_idx_assignment = center_nodes_idx_mapping[centers_assignment]

        rows = center_idx_assignment
        cols = np.arange(nodes_count)
        rows_summing_mat = sp.csr_matrix(
            (np.ones(nodes_count), (rows, cols)),
            shape=(centers_count, nodes_count),
            dtype=np.float32,
        )

        return rows_summing_mat

    @classmethod
    def _get_centers_flow_matrix(
        cls,
        flows_matrix: FlowMatrix,
        centers_assignment: np.ndarray,
    ) -> sp.csr_matrix:
        M = cls._get_rows_summings_matrix(centers_assignment=centers_assignment)
        center_flows = M @ flows_matrix @ M.T
        return center_flows

    @classmethod
    def _stabilize_raw_assignment(cls, raw_assignment: np.ndarray) -> np.ndarray:
        stable_assignment = np.full_like(
            raw_assignment, fill_value=NO_CENTER_IDX, dtype=np.int32
        )

        while NO_CENTER_IDX in stable_assignment:
            first_node_in_center_idx = stable_assignment.argmin()

            raw_assignment_center_nodes_idx = [first_node_in_center_idx]
            added_nodes = [first_node_in_center_idx]
            while len(added_nodes) > 0:
                new_leaf_nodes = raw_assignment[added_nodes]
                new_children_nodes = np.where(np.isin(raw_assignment, added_nodes))[0]
                potential_new_nodes = np.unique(
                    np.concatenate((new_leaf_nodes, new_children_nodes))
                )

                added_nodes = potential_new_nodes[
                    ~np.isin(potential_new_nodes, raw_assignment_center_nodes_idx)
                ]
                raw_assignment_center_nodes_idx.extend(added_nodes)

            stable_assignment[raw_assignment_center_nodes_idx] = (
                raw_assignment_center_nodes_idx[0]
            )

        return stable_assignment
