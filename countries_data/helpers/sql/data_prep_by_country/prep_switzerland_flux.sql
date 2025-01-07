-- Switzerland
SELECT
    LPAD("Residence Canton number", 2, '0') || LPAD("Residence Commune number", 4, '0') as NODE_1_CODE,
    "Residence Commune name" as NODE_1_NAME,
    LPAD("Work Canton number", 2, '0') || LPAD("Work Commune number", 4, '0') as NODE_2_CODE,
    "Work Commune name" as NODE_2_NAME,
    coalesce("2020", 2) as OUTGOING_FLOW
FROM
    commuter_flow.commuter_flow_switzerland