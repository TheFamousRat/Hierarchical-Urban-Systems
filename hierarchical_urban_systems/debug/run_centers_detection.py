from hierarchical_urban_systems.centers_detector.centers_detector import (
    CenterDetector,
)
from hierarchical_urban_systems.constants import COUNTRIES_DATA_ROOT
from hierarchical_urban_systems.flows_handler.country import Country
from hierarchical_urban_systems.flows_handler.flows_handler import FlowsHandler
from hierarchical_urban_systems.utils.debug_utils import (
    save_center_flows,
    show_assignment_performance,
)


def main() -> None:
    country = Country.SWITZERLAND
    country_data_root = COUNTRIES_DATA_ROOT / country.value

    flows_handler = FlowsHandler.from_path(root_folder_path=country_data_root)

    detector = CenterDetector(
        flows_matrix=flows_handler.flows_matrix,
    )

    leveled_assignments = detector.get_leveled_assignments(min_level=0, max_level=20)

    flows_handler.save_leveled_assignment(
        leveled_assignment=leveled_assignments,
        node_sizes=detector.node_sizes,
        min_center_size=1000.0,
        save_node_names=True,
    )

    save_center_flows(
        flows_matrix=flows_handler.flows_matrix,
        detector=detector,
        flows_handler=flows_handler,
        center_level=2,
        flows_degree=0,
        save_name="direct_center_flows",
    )

    save_center_flows(
        flows_matrix=flows_handler.flows_matrix,
        detector=detector,
        flows_handler=flows_handler,
        center_level=2,
        flows_degree=1,
        save_name="indirect_center_flows",
    )

    show_assignment_performance(
        detector=detector,
        flows_handler=flows_handler,
    )


if __name__ == "__main__":
    main()
