'''
This script uses python gerber library to read and parse any gerber file.
Then uses shapely to create outline gcode and holes gcode.
'''
from __future__ import annotations
import gerber
from shapely import Point, MultiPoint, LineString, LinearRing, box, Polygon
from matplotlib.patches import Ellipse
from copy import deepcopy
import turtle
import random

class GerberToShapely:
    '''
    This class converts gerber shape objects (also known as primitives) to shapely shape objects
    '''
    def __new__(cls, object_to_convert):
        '''
        special constructor to returnt the correct shapely object
        '''
        if not issubclass(type(object_to_convert), gerber.primitives.Primitive):
            raise ValueError("The object passed is not a gerber library shape object. (not a Primitive() object)")

        # setting the mapping method
        cls.set_class_convert_map()

        return cls.CONVERT_METHOD_MAP[type(object_to_convert)](object_to_convert)

    @classmethod
    def set_class_convert_map(cls):
        '''
        just sets the class variable dictionary which maps the gerber primitive datatype to its respective conersion method
        '''
        cls.CONVERT_METHOD_MAP = {  gerber.primitives.AMGroup: cls.to_amgroup,
                          gerber.primitives.Arc: cls.to_arc,
                          gerber.primitives.ChamferRectangle: cls.to_chamfer_rectangle,
                          gerber.primitives.Circle: cls.to_circle,
                          gerber.primitives.Diamond: cls.to_diamond,
                          gerber.primitives.Donut: cls.to_donut,
                          gerber.primitives.Drill: cls.to_drill,
                          gerber.primitives.Ellipse: cls.to_ellipse,
                          gerber.primitives.Line: cls.to_line,
                          gerber.primitives.Obround: cls.to_obround,
                          gerber.primitives.Outline: cls.to_outline,
                          gerber.primitives.Polygon: cls.to_polygon,
                          gerber.primitives.Rectangle: cls.to_rectangle,
                          gerber.primitives.Region: cls.to_region,
                          gerber.primitives.RoundButterfly: cls.to_round_butterfly,
                          gerber.primitives.RoundRectangle: cls.to_round_rectangle,
                          gerber.primitives.Slot: cls.to_slot,
                          gerber.primitives.SquareButterfly: cls.to_square_butterfly,
                          gerber.primitives.SquareRoundDonut: cls.to_square_round_donut,
                          gerber.primitives.TestRecord: cls.to_test_record}

    @classmethod
    def to_amgroup(cls, object_to_convert: gerber.primitives.Primitive) -> Polygon:
        '''
        AMGroup stands for Apt Macro Group, it's made of a list of Outline objects and other shapes like Circle or Obround
        '''
        polygon_list = []
        for shape in object_to_convert.primitives:
            print(shape)
            print(GerberToShapely(shape))
            polygon_list.append(GerberToShapely(shape))

        whole_thing = polygon_list[0]
        for polygon in polygon_list[1:]:
            whole_thing.union(polygon)

        return whole_thing

    @classmethod
    def to_arc(cls, object_to_convert: gerber.primitives.Primitive) -> Polygon:
        '''

        '''
        raise NotImplementedError("Arc primitive gerber object convertion to Shapely method still not implemented")
    
    @classmethod
    def to_chamfer_rectangle(cls, object_to_convert: gerber.primitives.Primitive) -> Polygon:
        '''

        '''
        raise NotImplementedError("ChamferRectangle primitive gerber object convertion to Shapely method still not implemented")

    @classmethod
    def to_circle(cls, object_to_convert: gerber.primitives.Primitive) -> Polygon:
        '''

        '''
        return Point(object_to_convert.position[0], object_to_convert.position[1]).buffer(object_to_convert.diameter/2)

    @classmethod
    def to_diamond(cls, object_to_convert: gerber.primitives.Primitive) -> Polygon:
        '''

        '''
        raise NotImplementedError("Diamond primitive gerber object convertion to Shapely method still not implemented")

    @classmethod
    def to_donut(cls, object_to_convert: gerber.primitives.Primitive) -> Polygon:
        '''

        '''
        raise NotImplementedError("Donut primitive gerber object convertion to Shapely method still not implemented")

    @classmethod
    def to_drill(cls, object_to_convert: gerber.primitives.Primitive) -> Polygon:
        '''

        '''
        raise NotImplementedError("Drill primitive gerber object convertion to Shapely method still not implemented")

    @classmethod
    def to_ellipse(cls, object_to_convert: gerber.primitives.Primitive) -> Polygon:
        '''

        '''
        ellipse = Ellipse((object_to_convert.position[0], object_to_convert.position[1]), object_to_convert.height*0.8, object_to_convert.width*0.8)

        return Polygon(LinearRing(ellipse.get_verts()))

    @classmethod
    def to_line(cls, object_to_convert: gerber.primitives.Primitive) -> LineString:
        '''

        '''
        if object_to_convert.aperture.diameter != 0:
            return Polygon(LineString([(object_to_convert.start[0], object_to_convert.start[1]), (object_to_convert.end[0], object_to_convert.end[1])]).buffer(object_to_convert.aperture.diameter/2).exterior)

        else:
            return LineString([(object_to_convert.start[0], object_to_convert.start[1]), (object_to_convert.end[0], object_to_convert.end[1])])

    @classmethod
    def to_obround(cls, object_to_convert: gerber.primitives.Primitive) -> LinearRing:
        '''

        '''
        # Step 1: create the base circle
        diameter = object_to_convert.height if object_to_convert.height < object_to_convert.width else object_to_convert.width
        radius = diameter/2
        circle = Point(object_to_convert.position).buffer(radius)

        # Step 2: divide the circle into 4 quarters
        x_min = object_to_convert.position[0] - radius
        x_max = object_to_convert.position[0] + radius
        y_min = object_to_convert.position[1] - radius
        y_max = object_to_convert.position[1] + radius

        circle_coords = list(circle.exterior.coords) 

        top_coord = (object_to_convert.position[0], y_max)
        right_coord = (x_max, object_to_convert.position[1])
        bottom_coord = (object_to_convert.position[0], y_min)
        left_coord = (x_min, object_to_convert.position[1])

        top_coord_ind = circle_coords.index(top_coord)
        top_coord_ind2 = top_coord_ind if circle_coords.count(top_coord) == 1 else -1
        right_coord_ind = circle_coords.index(right_coord)
        right_coord_ind2 = right_coord_ind if circle_coords.count(right_coord) == 1 else -1
        bottom_coord_ind = circle_coords.index(bottom_coord)
        bottom_coord_ind2 = bottom_coord_ind if circle_coords.count(bottom_coord) == 1 else -1
        left_coord_ind = circle_coords.index(left_coord)
        left_coord_ind2 = left_coord_ind if circle_coords.count(left_coord) == 1 else -1

        top_right_coords = circle_coords[top_coord_ind : right_coord_ind2]
        bottom_right_coords = circle_coords[right_coord_ind : bottom_coord_ind2]
        bottom_left_coords = circle_coords[bottom_coord_ind: left_coord_ind2]
        top_left_coords = circle_coords[left_coord_ind : top_coord_ind2]

        # Step 3: Find the 2 shifting transformations (if they exist)
        if object_to_convert.height > object_to_convert.width:
            # 2 vertical transformations for each two quarters
            shifting_value = (object_to_convert.height - object_to_convert.width)/2
            top_right_coords = [(coord[0], coord[1]+shifting_value) for coord in top_right_coords]
            top_left_coords = [(coord[0], coord[1]+shifting_value) for coord in top_left_coords]
            bottom_right_coords = [(coord[0], coord[1]-shifting_value) for coord in bottom_right_coords]
            bottom_left_coords = [(coord[0], coord[1]-shifting_value) for coord in bottom_left_coords]

        elif object_to_convert.height < object_to_convert.width:
            # 2 horizontal transformations for each two quarters
            shifting_value = (object_to_convert.width - object_to_convert.height)/2
            top_right_coords = [(coord[0]+shifting_value, coord[1]) for coord in top_right_coords]
            bottom_right_coords = [(coord[0]+shifting_value, coord[1]) for coord in bottom_right_coords]
            top_left_coords = [(coord[0]-shifting_value, coord[1]) for coord in top_left_coords]
            bottom_left_coords = [(coord[0]-shifting_value, coord[1]) for coord in bottom_left_coords]

        else:
            # No transformations
            pass

        joined_quarters_coords = top_right_coords
        joined_quarters_coords.extend(bottom_right_coords)
        joined_quarters_coords.extend(bottom_left_coords)
        joined_quarters_coords.extend(top_left_coords)

        return Polygon(LinearRing(joined_quarters_coords))


    @classmethod
    def to_outline(cls, object_to_convert: gerber.primitives.Primitive) -> LinearRing:
        '''
        like AMGroup, it has the .primitives attribute and contain a bunch of Line objects
        '''
        # checking my theory that outline only contains Line
        for shape in object_to_convert.primitives:
            if type(shape) != gerber.primitives.Line:
                raise ValueError("I thought Outline only contains Line object ;(")

            if shape.aperture.diameter != 0:
                raise ValueError("I thought outline gerber.primitives.Line objects don't have a thickness ;(")

        coord_list = []
        for line in object_to_convert.primitives:
            coord_list.append(line.start)
            coord_list.append(line.end)

        return Polygon(LinearRing(coord_list))

    @classmethod
    def to_polygon(cls, object_to_convert: gerber.primitives.Primitive) -> LinearRing:
        '''

        '''
        raise NotImplementedError("Polygon primitive gerber object convertion to Shapely method still not implemented")

    @classmethod
    def to_rectangle(cls, object_to_convert: gerber.primitives.Primitive) -> LinearRing:
        '''

        '''
        rectangle = box(object_to_convert.lower_left[0], object_to_convert.lower_left[1], object_to_convert.upper_right[0], object_to_convert.upper_right[1])
        return Polygon(LinearRing(list(rectangle.exterior.coords)))


    @classmethod
    def to_region(cls, object_to_convert: gerber.primitives.Primitive) -> LinearRing:
        '''

        '''
        raise NotImplementedError("Region primitive gerber object convertion to Shapely method still not implemented")

    @classmethod
    def to_round_butterfly(cls, object_to_convert: gerber.primitives.Primitive) -> LinearRing:
        '''

        '''
        raise NotImplementedError("RoundButterfly primitive gerber object convertion to Shapely method still not implemented")

    @classmethod
    def to_round_rectangle(cls, object_to_convert: gerber.primitives.Primitive) -> LinearRing:
        '''

        '''
        raise NotImplementedError("RoundRectangle primitive gerber object convertion to Shapely method still not implemented")

    @classmethod
    def to_slot(cls, object_to_convert: gerber.primitives.Primitive) -> LinearRing:
        '''

        '''
        raise NotImplementedError("Slot primitive gerber object convertion to Shapely method still not implemented")

    @classmethod
    def to_square_butterfly(cls, object_to_convert: gerber.primitives.Primitive) -> LinearRing:
        '''

        '''
        raise NotImplementedError("SquareButterfly primitive gerber object convertion to Shapely method still not implemented")

    @classmethod
    def to_square_round_donut(cls, object_to_convert: gerber.primitives.Primitive) -> LinearRing:
        '''

        '''
        raise NotImplementedError("SquareRoundDonut primitive gerber object convertion to Shapely method still not implemented")

    @classmethod
    def to_test_record(cls, object_to_convert: gerber.primitives.Primitive) -> LinearRing:
        '''

        '''
        raise NotImplementedError("TestRecord primitive gerber object convertion to Shapely method still not implemented")


def visualize(line_string: LineString, hide_turtle=True, speed=0, x_offset=40, y_offset=20, line_width=1.5, multiplier=8, terminate=False) -> None:
    '''
    visualizes the linked list
    '''
    if type(line_string) != LineString and type(line_string) != LinearRing and type(line_string) != Polygon:
        raise ValueError("Must be of type shapely LineString")

    turtle_window_size_x = 850
    turtle_window_size_y = 580
    turtle.Screen().setup(turtle_window_size_x, turtle_window_size_y)
    skk = turtle.Turtle()
    turtle.width(line_width)
    turtle.speed(speed)
    if hide_turtle:
        turtle.hideturtle()
    else:
        turtle.showturtle()

    colors = ['black', 'red', 'blue', 'light blue', 'green', 'brown', 'dark green', 'orange', 'gray', 'indigo']
    color = random.choice(colors)
    # while color in Graph.used_colors:
    #     color = random.choice(colors)

    turtle.pencolor(color)
    if type(line_string) == Polygon:
        coord_list = list(line_string.exterior.coords)

    else:
        coord_list = list(line_string.coords)

    turtle.up()
    turtle.setpos((coord_list[0][0] - x_offset) * multiplier, (coord_list[0][1] - y_offset) * multiplier)
    turtle.down()
    for coord in coord_list[1:-1]:
        turtle.setpos((coord[0] - x_offset) * multiplier, (coord[1] - y_offset) * multiplier)

    turtle.setpos((coord_list[-1][0] - x_offset) * multiplier, (coord_list[-1][1] - y_offset) * multiplier)
    # if coord_list[0] == coord_list[-1]:
    #     turtle.setpos((coord_list[0][0] - x_offset) * multiplier, (coord[1] - y_offset) * multiplier)

    # Graph.used_colors.add(color)
    # if len(Graph.used_colors) == len(colors):
    #     print('\n\n!!!!!!!!!! COLORS RESET !!!!!!!!!!!!!!!!!\n\n')
    #     Graph.used_colors = set()

    if terminate:
        turtle.done()

def visualize_group(group):
    for num, sth in enumerate(group[:-1]):
        visualize(sth)
        print(num)
    visualize(group[-1], terminate=True)


if __name__ == '__main__':
    gerber_file = 'gerber_files/limit_switch-F_Cu.gbr'
    
    gerber_obj = gerber.read(gerber_file)

    shapely_objects = []
    for num, gerber_primitive in enumerate(gerber_obj.primitives):
        shapely_objects.append(GerberToShapely(gerber_primitive))


    # IT WORKS :D !!!
    whole_thing = shapely_objects[0]
    for num, shapely_object in enumerate(shapely_objects[1:]):
        whole_thing = whole_thing.union(shapely_object)

    whole_thing = list(whole_thing.geoms)
    visualize_group(whole_thing)

    #TODO: figure out how to MIRROR the gerber file
    #TODO: figure out how to move the gerber file




    
