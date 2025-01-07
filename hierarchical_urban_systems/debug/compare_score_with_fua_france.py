from pathlib import Path
import numpy as np
import pandas

from hierarchical_urban_systems.centers_detector.flows_feature_extractor import (
    DistanceType,
    FlowsFeatureExtractor,
)
from hierarchical_urban_systems.centers_detector.nodes_assignment_score import (
    NodesAssignmentScore,
)
from hierarchical_urban_systems.constants import COUNTRIES_DATA_ROOT
from hierarchical_urban_systems.flows_handler.country import Country
from hierarchical_urban_systems.flows_handler.flows_handler import FlowsHandler


def _get_fua_assignment(
    flows_handler: FlowsHandler, country_data_root: Path
) -> np.ndarray:
    aa_df = pandas.read_csv(
        country_data_root / "data" / "src" / "AAV2020_au_01-01-2020_v1.csv"
    )
    aa_df = aa_df[["CODGEO", "LIBGEO", "AAV2020", "LIBAAV2020"]]

    code_to_index_mapping: list[int] = [
        flows_handler.node_code_to_index.get(code, -1) for code in aa_df["CODGEO"]
    ]
    aa_df["NODE_INDEX"] = code_to_index_mapping

    fua_assignment = np.arange(flows_handler.nodes_count, dtype=np.int32)

    non_isolated_communes = aa_df[
        (aa_df["AAV2020"] != "000") & (aa_df["NODE_INDEX"] != -1)
    ]

    center_communes = non_isolated_communes[
        [
            center_name.startswith(node_name)
            for center_name, node_name in zip(
                non_isolated_communes["LIBAAV2020"], non_isolated_communes["LIBGEO"]
            )
        ]
    ]
    center_code_to_node_code = dict(center_communes[["AAV2020", "CODGEO"]].values)
    center_code_to_node_code = center_code_to_node_code | {
        "GEN": "SUC1L",
        "LUX": "LU320",
        "SAR": "AL157",
        "221": "62617",
        "LAU": "SU96F",
        "CHA": "BE523",
        "BAL": "SU611",
        "MON": "MO001",
    }
    unassigned_communes = non_isolated_communes[
        ~non_isolated_communes["AAV2020"].isin(set(center_code_to_node_code.keys()))
    ]
    assert len(unassigned_communes) == 0

    for center_code, node_code in center_code_to_node_code.items():
        center_members = non_isolated_communes[
            non_isolated_communes["AAV2020"] == center_code
        ]
        center_node_index = flows_handler.node_code_to_index[node_code]
        fua_assignment[center_members["NODE_INDEX"]] = center_node_index

    return fua_assignment


def compare_hus_score_with_fua_france() -> None:
    country = Country.FRANCE
    country_data_root = COUNTRIES_DATA_ROOT / country.value

    flows_handler = FlowsHandler.from_path(root_folder_path=country_data_root)

    fua_assignment = _get_fua_assignment(
        flows_handler=flows_handler, country_data_root=country_data_root
    )

    node_sizes = flows_handler.flows_matrix.sum(axis=1).A[:, 0]

    flows_handler.save_leveled_assignment(
        leveled_assignment=np.vstack(
            (np.arange(flows_handler.nodes_count), fua_assignment)
        ),
        node_sizes=node_sizes,
        min_center_size=1000.0,
        output_file_name="fua_assignment",
    )

    saved_assignments = flows_handler.read_saved_assignment()

    fua_score_direct_flows = NodesAssignmentScore.get_exhaustivity_score_for_assignment(
        flows_matrix=flows_handler.flows_matrix, assignment=fua_assignment
    )
    proposed_score_direct_flows = (
        NodesAssignmentScore.get_exhaustivity_score_for_assignment(
            flows_matrix=flows_handler.flows_matrix,
            assignment=saved_assignments[5, :],
        )
    )
    print("===DIRECT FLOWS===")
    print(f"Score with FUA on direct flows: {fua_score_direct_flows}")
    print(
        f"Score with proposed algorithm on direct flows: {proposed_score_direct_flows}"
    )

    local_flows = FlowsFeatureExtractor.get_local_flows_matrix(
        flows_matrix=flows_handler.flows_matrix,
        node_sizes=node_sizes,
        distance_type=DistanceType.GEOMETRIC_MEAN,
    )

    fua_score_local_flows = NodesAssignmentScore.get_exhaustivity_score_for_assignment(
        flows_matrix=local_flows, assignment=fua_assignment
    )
    proposed_score_local_flows = (
        NodesAssignmentScore.get_exhaustivity_score_for_assignment(
            flows_matrix=local_flows,
            assignment=saved_assignments[2, :],
        )
    )
    print("===LOCAL FLOWS===")
    print(f"Score with FUA on local flows: {fua_score_local_flows}")
    print(f"Score with proposed algorithm on local flows: {proposed_score_local_flows}")


if __name__ == "__main__":
    compare_hus_score_with_fua_france()
