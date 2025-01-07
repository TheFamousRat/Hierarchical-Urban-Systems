import numpy as np
import scipy.sparse as sp  # type: ignore[import-untyped]

from hierarchical_urban_systems.centers_detector.nodes_assignment_score import (
    NodesAssignmentScore,
)


def test_it_produces_coherent_scores_for_extreme_assignments(
    flows_matrix: sp.csr_matrix,
) -> None:
    nodes_count = flows_matrix.shape[0]

    lone_centers_assignment = np.arange(nodes_count, dtype=np.int32)
    lone_centers_score = NodesAssignmentScore.get_exhaustivity_score_for_assignment(
        flows_matrix=flows_matrix, assignment=lone_centers_assignment
    )
    assert lone_centers_score.all_nodes_alone_score is not None
    assert np.isclose(
        lone_centers_score.proposed_score, lone_centers_score.all_nodes_alone_score
    )

    one_center_assignment = np.full(shape=nodes_count, fill_value=0, dtype=np.int32)
    one_center_score = NodesAssignmentScore.get_exhaustivity_score_for_assignment(
        flows_matrix=flows_matrix, assignment=one_center_assignment
    )
    assert one_center_score.all_nodes_together_score is not None
    assert np.isclose(
        one_center_score.proposed_score, one_center_score.all_nodes_together_score
    )
