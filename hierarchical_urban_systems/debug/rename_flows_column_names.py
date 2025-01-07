import pandas
from hierarchical_urban_systems.constants import (
    COUNTRIES_DATA_ROOT,
    INCOMING_FLOW_FIELD_NAME,
    SOURCE_NODE_NAME_FIELD_NAME,
    SOURCE_NODE_CODE_FIELD_NAME,
    TARGET_NODE_CODE_FIELD_NAME,
    TARGET_NODE_NAME_FIELD_NAME,
)
from hierarchical_urban_systems.flows_handler.country import Country


def main() -> None:
    for country in Country:
        country_data_root = COUNTRIES_DATA_ROOT / country.value
        flows_path = country_data_root / "data/incoming_flows.pkl"
        flows_df = pandas.read_pickle(flows_path)

        flows_df.columns = [
            TARGET_NODE_CODE_FIELD_NAME,
            TARGET_NODE_NAME_FIELD_NAME,
            SOURCE_NODE_CODE_FIELD_NAME,
            SOURCE_NODE_NAME_FIELD_NAME,
            INCOMING_FLOW_FIELD_NAME,
        ]
        pandas.to_pickle(flows_df, flows_path)


if __name__ == "__main__":
    main()
