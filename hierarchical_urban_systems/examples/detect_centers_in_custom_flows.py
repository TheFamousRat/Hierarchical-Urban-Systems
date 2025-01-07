import json
import scipy.sparse as sp  # type: ignore [import-untyped]
from pathlib import Path
from hierarchical_urban_systems.centers_detector.centers_detector import CenterDetector
from hierarchical_urban_systems.centers_detector.nodes_assignment_score import (
    NodesAssignmentScore,
)
from hierarchical_urban_systems.flows_handler.flows_handler import FlowsHandler


def detect_centers_in_custom_flows() -> None:
    # The only input required to run the algorithm is a flows matrix
    # For optimization purposes, this matrix is expected to be provided as a sparse matrix
    data_folder = Path(__file__).parent / "example_data"
    flows_matrix = sp.load_npz(data_folder / "bilateral_flows_switzerland.npz")

    # Optionally, a mapping of the nodes' codes to their names can be provided.
    # These names will be included in the output, making it easier to read through and understand.
    # The order of nodes in the mapping must be the same of the order of flows in the source matrix
    with open(data_folder / "node_code_to_name_mapping.json", "r") as f:
        node_code_to_name = json.load(fp=f)

    # The FlowsHandler class provides utilities to read flows data and save centers extraction results
    # It is not necessary to use it to run the algorithm.
    # If some data necessary to its initialization is missing, you can safely omit it.
    flows_handler = FlowsHandler.from_flows_and_mapping(
        output_folder=data_folder,
        flows_matrix=flows_matrix,
        node_code_to_name=node_code_to_name,
    )

    # The CenterDetector is the main class of this repository. Given a flow matrix, it will produce leveled assignments
    # of its nodes.
    detector = CenterDetector(
        flows_matrix=flows_handler.flows_matrix,
    )

    # This is the main I/O method of CenterDetector. It will pre-compute the assignments of the nodes, from level 0 (every node its center)
    # to 10. The computation is done only once per level and is then stored: calling this method again has no cost
    leveled_assignments = detector.get_leveled_assignments(min_level=0, max_level=10)

    # All the provided levels will be saved, eg here each node will have its assignment from level 0 to 10 stored.
    # The output file is a .csv, and can be filtered to show only centers of a certain size. Here, centers that never
    # reach a size larger than 1000 [commuters] will be omitted from the output.
    flows_handler.save_leveled_assignment(
        leveled_assignment=leveled_assignments,
        node_sizes=detector.node_sizes,
        min_center_size=1000.0,
        save_node_names=True,
    )

    # This class proposes a novel way to evaluate the quality of the assignment. You can try it for different flows and
    # different assignment and see which combination gives you the highest score.
    # Three scores are computed by the line below: one with the proposed assignment, one if all nodes were together,
    # and one if all nodes were their own center. This serves as a way to compare the proposed assignment to extreme clustering scenarios.
    score = NodesAssignmentScore.get_exhaustivity_score_for_assignment(
        flows_matrix=flows_handler.flows_matrix,
        assignment=detector.get_assignment_of_level(level=5),
    )
    print("Score:", score)


if __name__ == "__main__":
    detect_centers_in_custom_flows()
