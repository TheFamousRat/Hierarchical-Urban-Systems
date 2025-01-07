from pathlib import Path

import numpy as np
import pandas
import pytest
import scipy.sparse as sp  # type: ignore[import-untyped]
from pandas import DataFrame

from hierarchical_urban_systems.constants import (
    TARGET_NODE_CODE_FIELD_NAME,
    SOURCE_NODE_NAME_FIELD_NAME,
    SOURCE_NODE_CODE_FIELD_NAME,
    TARGET_NODE_NAME_FIELD_NAME,
    INCOMING_FLOW_FIELD_NAME,
)
from hierarchical_urban_systems.flows_handler.flows_handler import FlowsHandler


@pytest.fixture()
def incoming_flows_dataframe() -> DataFrame:
    node_codes = ["A", "B", "C", "D"]
    node_names = ["Big center", "Suburb", "Secondary center", "Isolated node"]

    start_node_idx = [0, 0, 0, 0, 1, 1, 1, 2, 2, 2, 3]
    dest_node_idx = [0, 1, 2, 3, 0, 1, 2, 0, 1, 2, 3]
    df_data = {
        TARGET_NODE_CODE_FIELD_NAME: [node_codes[idx] for idx in start_node_idx],
        TARGET_NODE_NAME_FIELD_NAME: [node_names[idx] for idx in start_node_idx],
        SOURCE_NODE_CODE_FIELD_NAME: [node_codes[idx] for idx in dest_node_idx],
        SOURCE_NODE_NAME_FIELD_NAME: [node_names[idx] for idx in dest_node_idx],
        INCOMING_FLOW_FIELD_NAME: [
            20.0,
            11.0,
            3.0,
            1.0,
            6.0,
            8.0,
            3.0,
            2.0,
            1.0,
            12.0,
            8.0,
        ],
    }

    incoming_flows_df = pandas.DataFrame(df_data)

    return incoming_flows_df


def test_it_reads_incoming_flows_from_file(
    tmp_path: Path, incoming_flows_dataframe: DataFrame
) -> None:
    data_path = tmp_path / "data"
    data_path.mkdir()

    incoming_flows_dataframe.to_pickle(path=str(data_path / "incoming_flows.pkl"))

    flows_handler = FlowsHandler.from_path(root_folder_path=tmp_path)

    incoming_flows_matrix = sp.csr_matrix(
        np.array(
            [
                [
                    20,
                    11,
                    3,
                    1,
                ],
                [
                    6,
                    8,
                    3,
                    0,
                ],
                [
                    2,
                    1,
                    12,
                    0,
                ],
                [0, 0, 0, 8],
            ],
            dtype=np.float32,
        )
    )
    expected_bilateral_matrix = (
        incoming_flows_matrix
        + incoming_flows_matrix.T
        - sp.diags(incoming_flows_matrix.diagonal())
    )

    assert isinstance(flows_handler.flows_matrix, sp.spmatrix)
    assert np.allclose(
        expected_bilateral_matrix.todense(), flows_handler.flows_matrix.todense()
    )
    assert flows_handler.nodes_count == 4


def test_it_extracts_code_to_name_mapping(
    tmp_path: Path, incoming_flows_dataframe: DataFrame
) -> None:
    node_code_to_name = FlowsHandler._extract_node_code_to_name_mapping(
        flows_df=incoming_flows_dataframe
    )

    assert len(node_code_to_name) == 4
    assert node_code_to_name == {
        "A": "Big center",
        "B": "Suburb",
        "C": "Secondary center",
        "D": "Isolated node",
    }


def test_it_properly_saves_and_reads_assignment_without_size_filtering(
    tmp_path: Path, incoming_flows_dataframe: DataFrame
) -> None:
    data_path = tmp_path / "data"
    data_path.mkdir()

    incoming_flows_dataframe.to_pickle(path=str(data_path / "incoming_flows.pkl"))

    flows_handler = FlowsHandler.from_path(root_folder_path=tmp_path)

    assignment = np.array(
        [
            [0, 1, 2, 3],
            [0, 0, 2, 3],
            [0, 0, 3, 3],
            [0, 0, 3, 3],
            [3, 3, 3, 3],
        ],
        dtype=np.int32,
    )
    node_sizes = np.array([43, 29, 21, 9], dtype=np.float32)

    flows_handler.save_leveled_assignment(
        leveled_assignment=assignment, node_sizes=node_sizes, min_center_size=0.0
    )

    recovered_assignments = flows_handler.read_saved_assignment()

    assert np.allclose(assignment, recovered_assignments)


def test_it_properly_saves_and_reads_assignment_with_size_filtering(
    tmp_path: Path, incoming_flows_dataframe: DataFrame
) -> None:
    data_path = tmp_path / "data"
    data_path.mkdir()

    incoming_flows_dataframe.to_pickle(path=str(data_path / "incoming_flows.pkl"))

    flows_handler = FlowsHandler.from_path(root_folder_path=tmp_path)

    assignment = np.array(
        [
            [0, 1, 2, 3],
            [0, 0, 3, 3],
            [0, 0, 3, 3],
            [3, 3, 3, 3],
        ],
        dtype=np.int32,
    )
    node_sizes = np.array([43, 29, 21, 9], dtype=np.float32)

    flows_handler.save_leveled_assignment(
        leveled_assignment=assignment, node_sizes=node_sizes, min_center_size=80.0
    )

    expected_assignments = np.array(
        [
            [0, 1, 2, 3],
            [0, 1, 3, 3],
            [0, 1, 3, 3],
            [3, 3, 3, 3],
        ],
        dtype=np.int32,
    )

    recovered_assignments = flows_handler.read_saved_assignment()

    assert np.allclose(expected_assignments, recovered_assignments)
