from hierarchical_urban_systems.centers_detector.centers_detector import (
    CenterDetector,
)
from hierarchical_urban_systems.centers_detector.flows_feature_extractor import (
    FlowsFeatureExtractor,
    DistanceType,
)
from hierarchical_urban_systems.constants import COUNTRIES_DATA_ROOT
from hierarchical_urban_systems.flows_handler.country import Country
from hierarchical_urban_systems.flows_handler.flows_handler import FlowsHandler
from hierarchical_urban_systems.utils.debug_utils import (
    save_center_flows,
)


def main() -> None:
    country = Country.ITALY
    country_data_root = COUNTRIES_DATA_ROOT / country.value

    flows_handler = FlowsHandler.from_path(root_folder_path=country_data_root)

    detector = CenterDetector(
        flows_matrix=flows_handler.flows_matrix,
    )

    leveled_assignments = flows_handler.read_saved_assignment()

    detector._leveled_centers_assignment = leveled_assignments

    leveled_assignments = detector.get_leveled_assignments(min_level=0, max_level=20)

    flows_handler.save_leveled_assignment(
        leveled_assignment=leveled_assignments,
        node_sizes=detector.node_sizes,
        min_center_size=1000.0,
        save_node_names=True,
    )

    local_flows = FlowsFeatureExtractor.get_local_flows_matrix(
        flows_matrix=flows_handler.flows_matrix,
        node_sizes=detector.node_sizes,
        distance_type=DistanceType.GEOMETRIC_MEAN,
    )

    for i in [4, 7, 10]:
        save_center_flows(
            flows_matrix=local_flows,
            detector=detector,
            flows_handler=flows_handler,
            center_level=2,
            flows_degree=i,
            save_name=f"ilocal_center_flows_{i}",
        )


if __name__ == "__main__":
    main()
