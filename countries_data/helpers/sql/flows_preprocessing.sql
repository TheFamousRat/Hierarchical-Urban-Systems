DROP TABLE IF EXISTS outgoing_flows;

CREATE TEMP TABLE outgoing_flows AS (
-- Per-country flows formatting goes here
);

DROP TABLE IF EXISTS incoming_flows;

CREATE TEMP TABLE incoming_flows AS (
    SELECT
        NODE_2_CODE AS NODE_1_CODE,
        coalesce(NODE_2_NAME, 'UNKNOWN') AS NODE_1_NAME,
        NODE_1_CODE AS NODE_2_CODE,
        coalesce(NODE_1_NAME, 'UNKNOWN') AS NODE_2_NAME,
        OUTGOING_FLOW as INCOMING_FLOW
    FROM
        outgoing_flows
    ORDER BY
        NODE_1_CODE,
        NODE_1_NAME
);

SELECT
    *
FROM
    incoming_flows;