import logging

import numpy as np
import scipy.sparse as sp  # type: ignore[import-untyped]
from hierarchical_urban_systems.centers_detector.centers_detector import CenterDetector
from hierarchical_urban_systems.centers_detector.flows_feature_extractor import (
    FlowsFeatureExtractor,
    DistanceType,
)
from hierarchical_urban_systems.centers_detector.nodes_assignment_score import (
    NodesAssignmentScore,
)
from hierarchical_urban_systems.flows_handler.flows_handler import FlowsHandler
from hierarchical_urban_systems.utils.sp_utils import filter_small_values_from_matrix

_logger = logging.getLogger(name=__name__)
logging.basicConfig(level=logging.INFO)


def find_best_assignment_for_flows(
    detector: CenterDetector, flows_matrix: sp.spmatrix, start_level: int = 0
) -> tuple[NodesAssignmentScore, int]:
    best_score = NodesAssignmentScore(proposed_score=0.0)
    best_assignment_level = -1
    for level, assignment in enumerate(
        detector.iterate_computed_assignments(start_level=start_level)
    ):
        relative_assignment = detector.get_inter_levels_assignment(
            start_level=start_level, end_level=level
        )
        score_this_assignment = (
            NodesAssignmentScore.get_exhaustivity_score_for_assignment(
                flows_matrix=flows_matrix, assignment=relative_assignment
            )
        )

        if best_score.proposed_score > score_this_assignment.proposed_score:
            return best_score, best_assignment_level

        best_score = score_this_assignment
        best_assignment_level = level

    return best_score, best_assignment_level


def save_center_flows(
    flows_matrix: sp.spmatrix,
    detector: CenterDetector,
    flows_handler: FlowsHandler,
    center_level: int,
    flows_degree: int,
    save_name: str,
) -> None:
    centers_assignment = detector.get_assignment_of_level(level=center_level)
    indirect_center_flows = detector.get_center_flows_of_degree(
        flows_matrix=flows_matrix,
        centers_assignment=centers_assignment,
        flows_degree=flows_degree,
    )
    indirect_center_flows = filter_small_values_from_matrix(
        matrix=indirect_center_flows, min_value_threshold=5.0
    )
    center_nodes_idx = np.unique(centers_assignment)
    center_sizes = np.bincount(centers_assignment, detector.node_sizes)[
        center_nodes_idx
    ]
    flows_handler.save_flows(
        flows_mat=indirect_center_flows,
        save_name=save_name,
        nodes_idx=center_nodes_idx,
        node_sizes=center_sizes,
    )


def show_assignment_performance(
    detector: CenterDetector,
    flows_handler: FlowsHandler,
) -> None:
    local_flows = FlowsFeatureExtractor.get_local_flows_matrix(
        flows_matrix=flows_handler.flows_matrix,
        node_sizes=detector.node_sizes,
        distance_type=DistanceType.GEOMETRIC_MEAN,
    )
    best_score_local_flows, best_level_local_flows = find_best_assignment_for_flows(
        detector=detector, flows_matrix=local_flows
    )
    _logger.info(
        f"Best level for local flows: {best_level_local_flows}\nScore:"
        f" {best_score_local_flows}",
    )

    best_score_direct_flows, best_level_direct_flows = find_best_assignment_for_flows(
        detector=detector, flows_matrix=flows_handler.flows_matrix
    )
    _logger.info(
        f"Best level for direct flows: {best_level_direct_flows}\nScore:"
        f" {best_score_direct_flows}",
    )

    indirect_center_flows = detector.get_center_flows_of_degree(
        flows_matrix=flows_handler.flows_matrix,
        centers_assignment=detector.get_assignment_of_level(
            level=best_level_local_flows
        ),
        flows_degree=1,
    )
    best_score_indirect_flows, best_level_indirect_flows = (
        find_best_assignment_for_flows(
            detector=detector,
            flows_matrix=indirect_center_flows,
            start_level=best_level_local_flows,
        )
    )
    _logger.info(
        f"Best level for indirect flows: {best_level_indirect_flows}\nScore:"
        f" {best_score_indirect_flows}",
    )
