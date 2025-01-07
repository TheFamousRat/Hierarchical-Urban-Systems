import numpy as np

from hierarchical_urban_systems.centers_detector.centers_detector import CenterDetector


def test_it_stabilizes_complex_single_system_assignments() -> None:
    single_node_assignment = np.array([0], dtype=np.uint32)
    stabilized_single_node_assignment = CenterDetector._stabilize_raw_assignment(
        raw_assignment=single_node_assignment
    )

    assert len(single_node_assignment) == len(stabilized_single_node_assignment)
    assert len(np.unique(stabilized_single_node_assignment)) == 1

    loop_assignment_with_external_node = np.array([3, 3, 0, 2], dtype=np.uint32)
    stabilized_loop_assignment = CenterDetector._stabilize_raw_assignment(
        raw_assignment=loop_assignment_with_external_node
    )

    assert len(loop_assignment_with_external_node) == len(stabilized_loop_assignment)
    assert len(np.unique(stabilized_loop_assignment)) == 1

    hierarchical_assignment = np.array([3, 0, 3, 3, 0, 1], dtype=np.uint32)
    stabilized_hierarchical_assignment = CenterDetector._stabilize_raw_assignment(
        raw_assignment=hierarchical_assignment
    )

    assert len(hierarchical_assignment) == len(stabilized_hierarchical_assignment)
    assert len(np.unique(stabilized_hierarchical_assignment)) == 1


def test_it_stabilizes_assignment_with_multiple_systems() -> None:
    loop_assignment_with_lone_node = np.array([3, 3, 0, 2, 4], dtype=np.uint32)
    stabilized_loop_assignment = CenterDetector._stabilize_raw_assignment(
        raw_assignment=loop_assignment_with_lone_node
    )

    assert len(loop_assignment_with_lone_node) == len(stabilized_loop_assignment)
    assert len(np.unique(stabilized_loop_assignment)) == 2

    assignment_with_two_systems_and_a_lone_center = np.array(
        [0, 10, 10, 8, 3, 9, 4, 1, 4, 9, 9], dtype=np.uint32
    )
    stabilized_three_systems_assignment = CenterDetector._stabilize_raw_assignment(
        raw_assignment=assignment_with_two_systems_and_a_lone_center
    )

    assert len(assignment_with_two_systems_and_a_lone_center) == len(
        stabilized_three_systems_assignment
    )
    assert len(np.unique(stabilized_three_systems_assignment)) == 3
    # Checking that the nodes belonging to the same system were clustered together
    assert len(np.unique(stabilized_three_systems_assignment[[3, 4, 6, 8]])) == 1
    assert len(np.unique(stabilized_three_systems_assignment[[0]])) == 1
    assert len(np.unique(stabilized_three_systems_assignment[[2, 1, 10, 7, 5, 9]])) == 1


def test_it_properly_combines_center_flows() -> None:
    flows_matrix = np.array(
        [
            [20.0, 0.0, 10.0, 1.0, 2.0, 1.0, 0.0],
            [0.0, 5.0, 0.0, 3.0, 10.0, 10.0, 0.0],
            [10.0, 0.0, 7.0, 0.0, 0.0, 0.0, 0.0],
            [1.0, 3.0, 0.0, 10.0, 0.0, 0.0, 0.0],
            [2.0, 10.0, 0.0, 0.0, 5.0, 12.0, 0.0],
            [1.0, 10.0, 0.0, 0.0, 12.0, 5.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 27.0],
        ],
        dtype=np.float32,
    )
    assignment = np.array([0, 1, 0, 3, 1, 1, 6], dtype=np.int32)
    center_flows = CenterDetector._get_centers_flow_matrix(
        flows_matrix=flows_matrix, centers_assignment=assignment
    )
    expected_center_flows = np.array(
        [
            [47, 3, 1, 0],
            [3, 79, 3, 0],
            [1, 3, 10, 0],
            [0, 0, 0, 27],
        ],
        dtype=np.float32,
    )
    assert np.allclose(expected_center_flows, center_flows)
