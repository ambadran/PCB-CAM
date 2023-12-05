    ### Trying .union line strings
    # new_shape = shapely_objects[41].union(shapely_objects[42])
    # print(type(new_shape))
    # print(new_shape)
    # print(new_shape.geoms)
    # print(len(new_shape.geoms))
    # print(list(new_shape.geoms))
    # sub_shapes = list(new_shape.geoms)
    # for sub_shape in sub_shapes[:-1]:
    #     visualize(sub_shape)
    # visualize(sub_shapes[-1], terminate=True)

    ### Trying creating one polygon from line strings
    # shape1_coords = list(shapely_objects[41].coords)
    # shape2_coords = list(shapely_objects[42].coords)
    # coords_list = deepcopy(shape1_coords)
    # coords_list.extend(shape2_coords)
    # linear_ring = LinearRing(coords_list)
    # polygon = Polygon(linear_ring)
    # print(polygon.exterior)
    # visualize(polygon.exterior, terminate=True)

    ### Trying both ;/
    new_shape = shapely_objects[41].union(shapely_objects[42])
    # print(new_shape)
    test = LinearRing(new_shape.geoms)
    print(test)
    polygon = Polygon(test)
    print(polygon)



