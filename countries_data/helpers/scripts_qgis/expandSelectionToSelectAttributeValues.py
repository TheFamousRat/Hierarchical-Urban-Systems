"""
Lists all the values of a certain attribute in the selection,
and selects all the features with that same value for that
same attribute
"""

attribute_to_select: str = "assignment_center_2_code"
# attribute_to_select: str = "epci_code"
# attribute_to_select: str = "nouvelle_region"
# attribute_to_select: str = "nouveau_dep"
# attribute_to_select: str = "new_state"

layer = iface.activeLayer()
selected_features = list(layer.getSelectedFeatures())
selected_departements = {str(f[attribute_to_select]) for f in selected_features}

if None in selected_departements:
    selected_departements.remove(None)

filter_list = ",".join(
    ["'" + dep.replace("'", "\\'") + "'" for dep in selected_departements]
)
filter_str = ' "{}"IN({})'.format(attribute_to_select, filter_list)

layer.selectByExpression(filter_str)

layer.selectByIds(
    [f.id() for l in [selected_features, layer.getSelectedFeatures()] for f in l]
)
