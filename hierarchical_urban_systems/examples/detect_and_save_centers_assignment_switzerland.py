from hierarchical_urban_systems.centers_detector.centers_detector import (
    CenterDetector,
)
from hierarchical_urban_systems.centers_detector.nodes_assignment_score import (
    NodesAssignmentScore,
)
from hierarchical_urban_systems.constants import COUNTRIES_DATA_ROOT
from hierarchical_urban_systems.flows_handler.country import Country
from hierarchical_urban_systems.flows_handler.flows_handler import FlowsHandler


def detect_and_save_centers_assignment() -> None:
    # FlowsHandler is a utility class designed to help loading flows matrices and storing the extracted center assignments
    # It is decoupled from CenterDetector and thus not necessary to use.
    flows_handler = get_flows_handler_for_switzerland()

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


def get_flows_handler_for_switzerland() -> FlowsHandler:
    # In this example, we create a FlowsHandler object which will load flows information from the Switzerland information
    # we have gathered. Many other countries are present in this repo, feel free to play around with them.
    country = Country.SWITZERLAND
    country_data_root = COUNTRIES_DATA_ROOT / country.value

    flows_handler = FlowsHandler.from_path(root_folder_path=country_data_root)

    return flows_handler


if __name__ == "__main__":
    detect_and_save_centers_assignment()
