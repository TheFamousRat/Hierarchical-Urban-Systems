--Italy
SELECT
    f.NODE_1_CODE,
    a."Denomination (Italian/German)" as NODE_1_NAME,
    f.NODE_2_CODE,
    b."Denomination (Italian/German)" as NODE_2_NAME,
    f.OUTGOING_FLOW
FROM
    (
        SELECT
            NODE_1_CODE,
            NODE_2_CODE,
            SUM(OUTGOING_FLOW) AS OUTGOING_FLOW
        FROM
            (
                SELECT
                    CONCAT(
                        "Province of residence",
                        "Municipality of residence"
                    ) as NODE_1_CODE,
                    CONCAT(
                        "Usual province of study or work",
                        "Usual municipality of study or work"
                    ) as NODE_2_CODE,
                    coalesce(
                        "Number of individuals",
                        coalesce("Estimated number of individuals", 0)
                    ) as OUTGOING_FLOW
                FROM
                    commuter_flow.commuter_flow_italy
            )
        GROUP BY
            NODE_1_CODE,
            NODE_2_CODE
    ) f
    LEFT JOIN commuter_flow.stats_ville_italiennes a on a."Istat code of the municipality (alphanumeric format)" = f.NODE_1_CODE
    LEFT JOIN commuter_flow.stats_ville_italiennes b on b."Istat code of the municipality (alphanumeric format)" = f.NODE_2_CODE
ORDER BY
    NODE_1_CODE,
    OUTGOING_FLOW desc