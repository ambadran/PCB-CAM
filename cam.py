'''
This script uses python gerber library to read and parse any gerber file.
Then uses shapely to create outline gcode and holes gcode.
'''
from __future__ import annotations
import gerber
try:
    from shapely import Point, MultiPoint, LineString, LinearRing, box, Polygon
except ImportError:
    from shapely.geometry import Point, MultiPoint, LineString, LinearRing, box, Polygon

from matplotlib.patches import Ellipse
from copy import deepcopy
import turtle
import random

DEFAULT_RESOLUTION = 5

############# Adding features to imported classes #############

# 1: adding slicing feature to Point class from shapely
def point_getitem(self, index) -> float:
    '''
    Enable slicing of coordinate objects
    '''
    if index == 0:
        return self.x
    elif index == 1:
        return self.y
    elif index == 2:
        return self.z
    else:
        raise IndexError("Only X, Y, Z values available")

Point.__getitem__ = point_getitem

# 2: adding x-offset and y-offset to gerber class
def recenter_gerber_file(self, x_offset: int, y_offset: int) -> None:
    '''
    recenter the whole gerber file, self now contains the gerber file with recentered coordinates of everything

    # self.bounds = ((152.273, 200.773), (-108.331, -82.943))
    # x_min = 152.273
    # x_max = 200.773
    # y_min = -108.331
    # y_max = -82.943

    :param x_offset: wanted x offset from origin. if 0 then pcb will start at 0
    :param y_offset: wanted y offset from origin. if 0 then pcb will start at 0
    '''
    # Get X and Y, min and max
    bounds = self.bounds
    x_min = bounds[0][0]
    x_max = bounds[0][1]
    y_min = bounds[1][0]
    y_max = bounds[1][1]

    # Calculating the offset to be added to each coordinate in the gerber file
    x_offset = -x_min + x_offset
    y_offset = -y_min + y_offset

    # Changing the statements attribute, the .bounds method is a property method depending on .statements
    for stmt in self.statements:
        stmt.offset(x_offset, y_offset)

    #TODO: I think there might be a way to create a new gerber file from the new statements generated from this loop
    
    # Changing the primitive attribute
    for ind, primitive in enumerate(self.primitives):

        if type(primitive) == gerber.primitives.Line:
            self.primitives[ind].start = (primitive.start[0] + x_offset, primitive.start[1] + y_offset)
            self.primitives[ind].end = (primitive.end[0] + x_offset, primitive.end[1] + y_offset)

        else:
            self.primitives[ind].position = (primitive.position[0] + x_offset, primitive.position[1] + y_offset)

    # print(self.primitives[80].start)
    # self.primitives[80].start = (self.primitives[80].start[0] + x_offset, self.primitives[80].start[1] + y_offset)
    # print(self.primitives[80].start)

gerber.rs274x.GerberFile.recenter_gerber_file = recenter_gerber_file

# 3: adding mirror feature to gerber class
def gerber_mirror(self, x_y_axis: bool = True) -> None:
    '''
    Mirrors the gerber file (for DIP components)

    Procedure:
    Step-1: x OR y coordinate is *-1 depending on whether we want to mirror in x or y axis
    Step-2: recenter to (x_min, y_min) (which is measured before step 1!!) 
    Done :D

    :param x_y_axis: determines whether to mirror in x or y axis, default is x-axis mirroring
    '''
    # Get X and Y, min for step2
    bounds = self.bounds
    x_min = bounds[0][0]
    y_min = bounds[1][0]


    ### Step 1: *-1
    # *-1 the .statements, the .bounds method is a property method depending on .statements
    for stmt in self.statements:
        try:
            if x_y_axis:
                stmt.x = stmt.x*-1
            else:
                stmt.y = stmt.y*-1

        except AttributeError:
            pass  # if no .x or .y then it's not a coordinate statement, do nothing

        except TypeError:
            pass # if .x or .y is NoneType then it's not a coordinate statement, do nothing

    # *-1 the .primitives
    for ind, primitive in enumerate(self.primitives):

        if type(primitive) == gerber.primitives.Line:
            if x_y_axis:
                self.primitives[ind].start = (primitive.start[0]*-1, primitive.start[1])
                self.primitives[ind].end = (primitive.end[0]*-1, primitive.end[1])
            else:
                self.primitives[ind].start = (primitive.start[0], primitive.start[1]*-1)
                self.primitives[ind].end = (primitive.end[0], primitive.end[1]*-1)

        else:
            if x_y_axis:
                self.primitives[ind].position = (primitive.position[0]*-1, primitive.position[1])
            else:
                self.primitives[ind].position = (primitive.position[0], primitive.position[1]*-1)

    ### Step 2: recenter to original position
    self.recenter_gerber_file(x_min, y_min)


gerber.rs274x.GerberFile.mirror = gerber_mirror


###############################################################



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
        print(f"Visualizaing Trace number: {num}")
    visualize(group[-1], terminate=True)

def get_laser_coords(gerber_obj: gerber.rs274x.GerberFile, include_edge_cuts: bool=True, resolution: int = DEFAULT_RESOLUTION, debug: bool=False) -> list[list[Point]]:
    '''
    Get list of list of coordinates, each list is one continious piece of trace.

    Meant for laser gcode where the laser go to first coordinate in a list, turn laser on, go to all coordinates, then laser OFF, then
    go to first coordinate in the next list, turn laser on , go to all coordiantes, then laser OFF, etc..

    :param gerber: Gerber Object from the gerber library
    :param include_edge_cuts: includes the edge cuts as part of pcb laser marking process
    :param resolution: the number of decimal places for coordinates
    :param debug: enable debugging info and display laser motion
    :return: list of list of coordinates of one continious trace

    #TODO: implement include_edge_cuts functionality
    #TODO: think about whether to round here or in the gcode_tools functions
    '''
    shapely_objects = []
    for num, gerber_primitive in enumerate(gerber_obj.primitives):
        shapely_objects.append(GerberToShapely(gerber_primitive))

    whole_thing = shapely_objects[0]
    for num, shapely_object in enumerate(shapely_objects[1:]):
        whole_thing = whole_thing.union(shapely_object)

    whole_thing = list(whole_thing.geoms)
    coord_list_list = [list(polygon_.exterior.coords) for polygon_ in whole_thing]
    coord_list_list = [[Point( round(coord[0], resolution), round(coord[1], resolution) ) for coord in coord_list] for coord_list in coord_list_list]

    if debug:
        visualize_group(whole_thing)

    return coord_list_list

def get_holes_coords(gerber_obj: gerber.rs274x.GerberFile, resolution: int = DEFAULT_RESOLUTION) -> list[Point]:
    '''
    Gets list of coordinates where the spindle must go straight down in the Z axis to drill

    :param gerber: Gerber Object from the gerber library
    :param resolution: the number of decimal places for coordinates
    :return: list of holes coordinates
    '''
    coord_list = []
    for primitive in gerber_obj.primitives:
        if type(primitive) != gerber.primitives.Line:
            coord_list.append(Point( round(primitive.position[0], resolution), round(primitive.position[1], resolution)))

    return coord_list

def get_pen_coords(gerber_obj: gerber.rs274x.GerberFile) -> list[Point]:
    '''

    '''
    pass

if __name__ == '__main__':
    gerber_file = 'gerber_files/limit_switch-F_Cu 2.gbr'
    
    gerber_obj = gerber.read(gerber_file)
    #TODO: figure out how to MIRROR the gerber file
    #TODO: figure out how to move the gerber file


    print(gerber_obj.primitives[80].start)
    print(gerber_obj.bounds)
    # print(get_laser_coords(gerber_obj, debug=True))
    gerber_obj.recenter_gerber_file(2, 2)
    print(gerber_obj.primitives[80].start)
    print(gerber_obj.bounds)
    print(get_laser_coords(gerber_obj, debug=True))

    
