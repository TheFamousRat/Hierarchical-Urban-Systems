from __future__ import annotations
import logging
from pathlib import Path

import numpy as np
import pandas
import scipy.sparse as sp  # type: ignore[import-untyped]
import tqdm
from pandas import DataFrame

from hierarchical_urban_systems.alias import NodeCode, NodeName
from hierarchical_urban_systems.constants import (
    SOURCE_NODE_NAME_FIELD_NAME,
    SOURCE_NODE_CODE_FIELD_NAME,
    TARGET_NODE_NAME_FIELD_NAME,
    TARGET_NODE_CODE_FIELD_NAME,
    INCOMING_FLOW_FIELD_NAME,
    DEBUG_OUTPUT_FOLDER,
    DEFAULT_ASSIGNMENT_OUTPUT_FILE_NAME,
    TQDM_COLS_COUNT,
)

_logger = logging.getLogger(name=__name__)
logging.basicConfig(level=logging.INFO)


class FlowsHandler:
    def __init__(
        self,
        output_folder: Path,
        flows_matrix: sp.csr_matrix,
        node_index_to_code: dict[int, NodeCode],  # TODO: Make these optional ?
        node_index_to_name: dict[int, NodeName],
    ) -> None:
        self.output_folder = output_folder

        self.node_index_to_code = node_index_to_code
        self.node_index_to_name = node_index_to_name
        self.node_code_to_name: dict[NodeCode, NodeName] = {
            self.node_index_to_code[node_index]: self.node_index_to_name[node_index]
            for node_index in self.node_index_to_code
        }
        self.node_code_to_index: dict[NodeCode, int] = {
            node_code: node_index
            for node_index, node_code in self.node_index_to_code.items()
        }

        self.nodes_count = len(self.node_code_to_name)

        self.flows_matrix = flows_matrix

        self._debug_output_folder: Path | None = None

    @classmethod
    def from_flows_and_mapping(
        cls,
        output_folder: Path,
        flows_matrix: sp.csr_matrix,
        node_code_to_name: dict[NodeCode, NodeName],
    ) -> "FlowsHandler":
        node_index_to_code = {
            node_index: node_code
            for node_index, node_code in enumerate(node_code_to_name)
        }
        node_index_to_name = {
            node_index: node_code_to_name[node_code]
            for node_index, node_code in enumerate(node_code_to_name)
        }

        return cls(
            output_folder=output_folder,
            flows_matrix=flows_matrix,
            node_index_to_code=node_index_to_code,
            node_index_to_name=node_index_to_name,
        )

    @classmethod
    def from_path(cls, root_folder_path: Path) -> "FlowsHandler":
        """
        Convenience FlowsHandler constructor. To use this, the data needs to be structured as follows:
            root_folder_path/
            ├─ data/
            │  ├─ incoming_flows.pkl

        The output files (debug data, saved assignment) will be stored in the "data" folder.

        If your file structure does not match the one above, consider loading your data separately and then using this class's
        __init__.
        """
        _logger.info("Reading and formatting raw flows files...")
        data_folder_path = root_folder_path / "data"

        flows_file_path = data_folder_path / "incoming_flows.pkl"
        incoming_flows_df = cls._read_incoming_flows_file(
            flows_file_path=flows_file_path
        )

        _logger.info("Extracting names data from flows...")
        node_code_to_name = cls._extract_node_code_to_name_mapping(
            flows_df=incoming_flows_df
        )
        node_code_to_index = {
            node_code: node_index
            for node_index, node_code in enumerate(node_code_to_name)
        }

        _logger.info("Building initial flow matrix...")
        incoming_flows_matrix = cls._build_matrix_from_flows_dataframe(
            flows_df=incoming_flows_df, node_code_to_index=node_code_to_index
        )
        bilateral_flows_matrix = (
            incoming_flows_matrix
            + incoming_flows_matrix.T
            - sp.diags(incoming_flows_matrix.diagonal())
        )

        _logger.info("Flows initialization done.")

        return cls.from_flows_and_mapping(
            output_folder=data_folder_path,
            flows_matrix=bilateral_flows_matrix,
            node_code_to_name=node_code_to_name,
        )

    def _get_assignment_file_path(self, output_file_name: str) -> Path:
        return self.output_folder / f"{output_file_name}.csv"

    def read_saved_assignment(
        self,
        output_file_name: str = DEFAULT_ASSIGNMENT_OUTPUT_FILE_NAME,
    ) -> np.ndarray:
        assignment_file_path = self._get_assignment_file_path(
            output_file_name=output_file_name
        )

        _logger.info(f"Reading saved assignments at {assignment_file_path}...")
        assignments_df = pandas.read_csv(
            filepath_or_buffer=assignment_file_path, dtype=str
        )

        center_code_columns = [
            col_name
            for col_name in assignments_df.columns
            if col_name.endswith("_code")
        ]
        found_center_levels = len(center_code_columns)

        if found_center_levels < 1:
            raise RuntimeError("Found no center assignment columns.")

        _logger.info(
            f"Found {found_center_levels-1} levels of assignment, mapping each center"
            " node code to its matching index."
        )
        assignments = np.repeat(
            np.arange(self.nodes_count, dtype=np.int32)[None, :],
            axis=0,
            repeats=found_center_levels,
        )

        for center_level, center_code_column in tqdm.tqdm(
            enumerate(center_code_columns[1:], start=1),
            desc="Assignment level mapping restored",
            ncols=TQDM_COLS_COUNT,
        ):
            assignment_this_level = assignments_df[center_code_column]
            all_center_node_codes = set(assignment_this_level)

            if np.nan in all_center_node_codes:
                all_center_node_codes.remove(np.nan)

            assignments[center_level, :] = [
                (
                    node_index
                    if not pandas.notna(center_code)
                    else self.node_code_to_index[center_code]
                )
                for node_index, center_code in enumerate(
                    assignments_df[center_code_column]
                )
            ]

        return assignments

    def save_leveled_assignment(
        self,
        leveled_assignment: np.ndarray,
        node_sizes: np.ndarray,
        min_center_size: float = 1000.0,
        save_node_names: bool = True,
        output_file_name: str = DEFAULT_ASSIGNMENT_OUTPUT_FILE_NAME,
    ) -> None:
        center_node_max_size = np.zeros(shape=(self.nodes_count,), dtype=np.float64)
        for center_level in range(leveled_assignment.shape[0]):
            center_sizes_this_level = np.bincount(
                leveled_assignment[center_level, :],
                weights=node_sizes,
                minlength=self.nodes_count,
            )
            center_node_max_size = np.maximum(
                center_node_max_size, center_sizes_this_level
            )

        represent_center_idx = center_node_max_size >= min_center_size

        center_levels_count = leveled_assignment.shape[0]

        assignment_codes_by_level: list[list[str | None]] = [[]] * center_levels_count
        assignment_codes_by_level[0] = [
            self.node_index_to_code[i] for i in range(self.nodes_count)
        ]

        for center_level in range(1, center_levels_count):
            center_assignment_this_level = leveled_assignment[center_level, :]
            assignment_center_codes: list[str | None] = [
                (
                    self.node_index_to_code[center_node_idx]
                    if represent_center_idx[center_node_idx]
                    else None
                )
                for center_node_idx in center_assignment_this_level
            ]
            assignment_codes_by_level[center_level] = assignment_center_codes

        centers_df_data: dict[str, list[str | None]] = {}
        for center_level in range(center_levels_count):
            center_level_root_name = (
                f"center_{center_level}" if center_level > 0 else "node"
            )

            assignment_level_codes = assignment_codes_by_level[center_level]

            centers_df_data[center_level_root_name + "_code"] = assignment_level_codes

            if save_node_names:
                centers_df_data[center_level_root_name + "_name"] = [
                    None if code is None else self.node_code_to_name[code]
                    for code in assignment_level_codes
                ]

        centers_df = pandas.DataFrame(centers_df_data)

        assignment_file_path = self._get_assignment_file_path(
            output_file_name=output_file_name
        )
        _logger.info(f"Saving assignment at '{assignment_file_path}'")
        centers_df.to_csv(path_or_buf=assignment_file_path, index=False)

        for center_level in range(1, center_levels_count):
            _logger.info(
                " - Saved"
                f" {len(np.unique(leveled_assignment[center_level][represent_center_idx]))} centers"
                f" at level {center_level}"
            )
        _logger.info(f"{(~represent_center_idx).sum()} small centers were discarded.")

    @property
    def debug_output_folder(self) -> Path:
        if self._debug_output_folder is None:
            self._debug_output_folder = self.output_folder / DEBUG_OUTPUT_FOLDER
            self._debug_output_folder.mkdir(exist_ok=True)

        return self._debug_output_folder

    def save_flows(
        self,
        flows_mat: sp.csr_matrix,
        save_name: str,
        nodes_idx: np.ndarray | None = None,
        node_sizes: np.ndarray | None = None,
    ) -> None:
        path = self.debug_output_folder / f"{save_name}.csv"
        _logger.info(f"Saving {len(flows_mat.data)} flows at '{path}'")

        if nodes_idx is None:
            nodes_idx = np.arange(flows_mat.shape[0])

        flows_mat.eliminate_zeros()
        start_node_idx, dest_node_idx = flows_mat.nonzero()

        df_data = {
            "node_1_code": [
                self.node_index_to_code[nodes_idx[i]] for i in start_node_idx
            ],
            "node_1_name": [
                self.node_index_to_name[nodes_idx[i]] for i in start_node_idx
            ],
            "node_2_code": [
                self.node_index_to_code[nodes_idx[i]] for i in dest_node_idx
            ],
            "node_2_name": [
                self.node_index_to_name[nodes_idx[i]] for i in dest_node_idx
            ],
            "flow": flows_mat.data,
        }

        if node_sizes is not None:
            df_data["node_1_size"] = [node_sizes[i] for i in start_node_idx]
            df_data["node_2_size"] = [node_sizes[i] for i in dest_node_idx]

        flows_df = pandas.DataFrame(df_data)
        flows_df.to_csv(path_or_buf=path, index=False)

    def save_node_data(
        self,
        node_code: NodeCode,
        nodes_data_matrix: sp.csr_matrix,
        data_name: str | None = None,
    ) -> None:
        node_index = self.node_code_to_index[node_code]
        self._save_node_data_vector_as_csv(
            data_vector=nodes_data_matrix[node_index].todense().A[0, :],
            data_name=data_name,
        )

    @classmethod
    def _extract_node_code_to_name_mapping(
        cls,
        flows_df: DataFrame,
    ) -> dict[NodeCode, NodeName]:
        all_names = pandas.concat(
            [
                flows_df[[TARGET_NODE_CODE_FIELD_NAME, TARGET_NODE_NAME_FIELD_NAME]],
                flows_df[
                    [SOURCE_NODE_CODE_FIELD_NAME, SOURCE_NODE_NAME_FIELD_NAME]
                ].rename(
                    columns={
                        SOURCE_NODE_CODE_FIELD_NAME: TARGET_NODE_CODE_FIELD_NAME,
                        SOURCE_NODE_NAME_FIELD_NAME: TARGET_NODE_NAME_FIELD_NAME,
                    }
                ),
            ],
            ignore_index=True,
        )
        all_names = all_names.fillna("UNKNOWN")
        all_unique_names = all_names.value_counts().reset_index()

        node_code_to_name = dict(
            zip(
                all_unique_names[TARGET_NODE_CODE_FIELD_NAME],
                all_unique_names[TARGET_NODE_NAME_FIELD_NAME],
            )
        )
        node_code_to_name = dict(sorted(node_code_to_name.items()))

        return node_code_to_name

    @classmethod
    def _build_matrix_from_flows_dataframe(
        cls,
        flows_df: DataFrame,
        node_code_to_index: dict[NodeCode, int],
    ) -> sp.csr_matrix:
        nodes_count = len(node_code_to_index)

        rows_inds: list[int] = [
            node_code_to_index[node_code]
            for node_code in flows_df[TARGET_NODE_CODE_FIELD_NAME]
        ]
        cols_inds: list[int] = [
            node_code_to_index[node_code]
            for node_code in flows_df[SOURCE_NODE_CODE_FIELD_NAME]
        ]
        data: list[float] = list(flows_df[INCOMING_FLOW_FIELD_NAME])

        flow_matrix = sp.csr_matrix(
            (data, (rows_inds, cols_inds)),
            shape=(nodes_count, nodes_count),
            dtype=np.float32,
        ).tocsr()

        flow_matrix.eliminate_zeros()

        return flow_matrix

    @classmethod
    def _read_incoming_flows_file(cls, flows_file_path: Path) -> DataFrame:
        # TODO: Maybe more intuitive to read from outgoing flows ?
        _logger.info(f"Reading flows from file {flows_file_path}...")
        flows_df = pandas.read_pickle(
            filepath_or_buffer=flows_file_path,
        )

        _logger.info(f"Found {len(flows_df)} flows in file {flows_file_path}.")
        return flows_df

    def _save_node_data_vector_as_csv(
        self,
        data_vector: np.ndarray,
        data_name: str | None = None,
    ) -> None:
        if data_name is None:
            data_name = "data"

        node_code_to_data = {
            self.node_index_to_code[tgt_idx]: data_vector[tgt_idx]
            for tgt_idx in data_vector.argsort()[::-1]
        }
        _df = pandas.DataFrame(
            node_code_to_data.items(), columns=[TARGET_NODE_CODE_FIELD_NAME, data_name]
        )

        _df.to_csv(self.debug_output_folder / f"{data_name}.csv", index=False)
