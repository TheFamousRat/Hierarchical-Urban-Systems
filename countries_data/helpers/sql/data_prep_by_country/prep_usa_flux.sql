--USA
SELECT
	LPAD("Start County Code", 5, '0') as NODE_1_CODE,
	"Start County Name" as NODE_1_NAME,
	LPAD("Dest County Code", 5, '0') as NODE_2_CODE,
	"Dest County Name" as NODE_2_NAME,
	"Workers in Commuting Flow" as OUTGOING_FLOW
FROM
	commuter_flow.commuter_flow_usa