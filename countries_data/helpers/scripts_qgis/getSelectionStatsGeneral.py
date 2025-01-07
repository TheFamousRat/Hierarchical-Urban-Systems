surface_unit_to_km2 = 1e-0

possible_surface_area_var_names = {"surface", "ALAND", "gem_flaeche"}
possible_pop_var_names = {"POPULATION", "POP2022", "einwohnerzahl"}
possible_name_var_names = {
    "NAME",
    "NOM_COM",
    "epci_nom",
    "epci_ou_com",
    "name",
    "INSEE_DEP",
    "assignment_center_8_code",
}

layer = iface.activeLayer()
selected_features = [f for f in layer.getSelectedFeatures()]

if len(selected_features) == 0:
    raise RuntimeError("No feature selected")


def get_field_name_among_possibilities(possible_field_names: set[str]) -> str:
    selected_feature = next(layer.getSelectedFeatures())
    feature_field_names: set[str] = set(selected_feature.fields().names())
    matching_field_names = feature_field_names.intersection(possible_field_names)

    if len(matching_field_names) == 0:
        raise ValueError(
            f"No field in the selected features matches '{possible_field_names}'"
        )

    return next(iter(matching_field_names))


name_variable = get_field_name_among_possibilities(
    possible_field_names=possible_name_var_names
)
pop_variable = get_field_name_among_possibilities(
    possible_field_names=possible_pop_var_names
)
surface_variable = get_field_name_among_possibilities(
    possible_field_names=possible_surface_area_var_names
)


total_pop = 0
total_area = 0
largest_node_name = ""
largest_node_pop = -1
for feature in selected_features:
    feature_attributes = feature.attributeMap()
    total_pop += feature_attributes[pop_variable]
    total_area += feature_attributes[surface_variable]
    if feature[pop_variable] > largest_node_pop:
        largest_node_name = feature[name_variable]
        largest_node_pop = feature[pop_variable]

total_area_km2 = total_area * surface_unit_to_km2
print(f"Overall stats: {total_pop} inhabitants, {round(total_area_km2, 2)} km²")
print(f"Density: {round(total_pop / total_area_km2, 2)} people/km2")
print(f"Most populated node: '{largest_node_name}', {largest_node_pop} inhabitants")
