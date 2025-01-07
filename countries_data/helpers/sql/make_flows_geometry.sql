    WITH node_data AS (
        SELECT
            "INSEE_COM" as CODE,
            geometry
        FROM
            "communes"
    )
    SELECT
        *,
        st_geomfromtext(wkt) as geom
    FROM
        (
            SELECT
                f.*,
                st_astext(
                    makeline(
                        st_centroid(c1.geometry),
                        st_centroid(c2.geometry)
                    )
                ) as wkt
            FROM
                "all_flows" f
                LEFT JOIN node_data c1 ON f.node_1_code = c1.CODE
                LEFT JOIN node_data c2 ON f.node_2_code = c2.CODE
            WHERE
                f.node_1_code <= f.node_2_code
                AND FLOW >= 25.0
        )
    WHERE
        wkt is not NULL;