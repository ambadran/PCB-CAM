
# trying to create rounded corners with shapely
box_polygon = shapely_objects[7]
    buffer_size = box_polygon.minimum_clearance*0.4
    print(buffer_size)
    box_polygon = box_polygon.buffer(-buffer_size)
    box_polygon = box_polygon.buffer(buffer_size)
    print(box_polygon)
    visualize(box_polygon, terminate=True)

