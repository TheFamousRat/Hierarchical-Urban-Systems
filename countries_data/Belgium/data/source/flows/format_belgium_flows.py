from pathlib import Path
from typing import Any

import numpy as np
import pandas

raw_file = pandas.read_csv(
    filepath_or_buffer=Path(__file__).parent / "Pop_LPW_FR_25FEB15.csv",
    dtype={"CODE-INS": str},
)

name_rows = list(range(0, 1941, 3))
communes_names = raw_file["Lieu de résidence"][name_rows]
communes_codes = raw_file["CODE-INS"][name_rows]

relevant_rows_mask = [
    (c[2:] != "000") and (c not in ["03001", "02001", "01001", "20002", "20001"])
    for c in list(communes_codes)
]

communes_names = np.array(communes_names[relevant_rows_mask])
communes_codes = np.array(communes_codes[relevant_rows_mask])

commune_name_to_code_mapping = dict(zip(communes_names, communes_codes))

flows_rows = list(range(2, 1941, 3))

dataframe_data: dict[str, Any] = {
    "NODE_1_CODE": [],
    "NODE_1_NAME": [],
    "NODE_2_CODE": [],
    "NODE_2_NAME": [],
    "INCOMING_FLOW": [],
}
for tgt_comm_name, tgt_comm_code in commune_name_to_code_mapping.items():
    flows_to_tgt_comm = raw_file[tgt_comm_name][flows_rows][relevant_rows_mask]
    flows_to_tgt_comm = flows_to_tgt_comm.reset_index(drop=True)
    non_null_flows_mask = np.where(flows_to_tgt_comm > 0)[0]
    non_null_flows_count = len(non_null_flows_mask)

    dataframe_data["NODE_1_CODE"].extend([tgt_comm_code] * non_null_flows_count)
    dataframe_data["NODE_1_NAME"].extend([tgt_comm_name] * non_null_flows_count)
    dataframe_data["NODE_2_CODE"].extend(communes_codes[non_null_flows_mask].tolist())
    dataframe_data["NODE_2_NAME"].extend(communes_names[non_null_flows_mask].tolist())
    dataframe_data["INCOMING_FLOW"].extend(list(flows_to_tgt_comm[non_null_flows_mask]))

all_flows_df = pandas.DataFrame(data=dataframe_data)
target_dir = Path(__file__).parent.parent / "flows"
target_dir.mkdir(parents=True, exist_ok=True)
all_flows_df.to_csv(
    path_or_buf=target_dir / "incoming_flows.csv", index=False, quoting=1
)
