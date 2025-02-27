'''
This script uses python gerber library to read and parse any gerber file.
Then uses shapely to create outline gcode and holes gcode.
'''
from __future__ import annotations

import warnings
with warnings.catch_warnings():
    # suppressing a stupid syntax warning to convert 'is not' to '!='
    warnings.filterwarnings("ignore", category=SyntaxWarning)
    import gerber

try:
    from shapely import Point, MultiPoint, LineString, LinearRing, box, Polygon
except ImportError:
    from shapely.geometry import Point, MultiPoint, LineString, LinearRing, box, Polygon

from matplotlib.patches import Ellipse
from copy import deepcopy
import turtle
import random
import math
import numpy as np

# Screen Dimensions
DEVICE_W = 1440 # 2560
DEVICE_H = 1160 # 1600
START_X = 0
START_Y = 0


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

    # Step 1a: Changing the statements attribute, the .bounds method is a property method depending on .statements
    for stmt in self.statements:
        stmt.offset(x_offset, y_offset)

    # Step 1b: Changing the primitive attribute
    for primitive in self.primitives:
        primitive.offset(x_offset, y_offset)

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
    # Step1a: *-1 the .statements, the .bounds method is a property method depending on .statements
    for stmt in self.statements:
        if hasattr(stmt, 'x') and hasattr(stmt, 'y'):
            if type(stmt.x) in [int, float] and type(stmt.y) in [int, float]:
                if x_y_axis:
                    stmt.x = stmt.x*-1
                else:
                    stmt.y = stmt.y*-1
        #TODO: does start and end angle of gerber.primitives.Arc need changing?!?!?

    # Step1b: *-1 the .primitives
    for ind, primitive in enumerate(self.primitives):

        if type(primitive) == gerber.primitives.Line:
            if x_y_axis:
                self.primitives[ind].start = (primitive.start[0]*-1, primitive.start[1])
                self.primitives[ind].end = (primitive.end[0]*-1, primitive.end[1])
            else:
                self.primitives[ind].start = (primitive.start[0], primitive.start[1]*-1)
                self.primitives[ind].end = (primitive.end[0], primitive.end[1]*-1)

        elif type(primitive) == gerber.primitives.Region:
            for ind2, region_primitive in enumerate(primitive.primitives):
                if type(region_primitive) == gerber.primitives.Line:
                    if x_y_axis:
                        self.primitives[ind].primitives[ind2].start = (region_primitive.start[0]*-1, region_primitive.start[1])
                        self.primitives[ind].primitives[ind2].end = (region_primitive.end[0]*-1, region_primitive.end[1])

                    else:
                        self.primitives[ind].primitives[ind2].start = (region_primitive.start[0], region_primitive.start[1]*-1)
                        self.primitives[ind].primitives[ind2].end = (region_primitive.end[0], region_primitive.end[1]*-1)

                else:
                    # Assuming all primitives inside Region object is line
                    raise NotImplementedError("I thought all primitives inside a Region object is Line primitives only")

        elif type(primitive) == gerber.primitives.Arc:
            if x_y_axis:
                # self.primitives[ind].center = (primitive.center[0]*-1, primitive.center[1])
                primitive.offset(-primitive.center[0]+primitive.center[0]*-1, 0)

            else:
                # self.primitives[ind].center = (primitive.center[0], primitive.center[1]*-1)
                primitive.offset(0, -primitive.center[1]+primitive.center[1]*-1)

        else:
            # Check if this Gerber type is implemented
            try:
                tmp = GerberToShapely(primitive)
            except NotImplementedError:
                print(f"\nThis Gerber Object {type(primitive)} isn't implemented! \n\n")
                raise

            if x_y_axis:
                self.primitives[ind].position = (primitive.position[0]*-1, primitive.position[1])
            else:
                self.primitives[ind].position = (primitive.position[0], primitive.position[1]*-1)

    ### Step 2: recenter to original position
    self.recenter_gerber_file(x_min, y_min)


gerber.rs274x.GerberFile.mirror = gerber_mirror

# 4: adding 90 degree rotation to invert width and height
def rotate_point(point: tuple[float, float], angle_degrees) -> tuple[float, float]:
    '''
    given a shapely.Point argument, this function will use matrix dot multiplication 
    to multiply the given 2d coordinate to rotate it angle_degrees, then 
    return a shapely.Point
    '''
    # Unpack the point tuple
    x, y = point[0], point[1]

    # Convert angle from degrees to radians
    angle_radians = math.radians(angle_degrees)

    # Calculate the cosine and sine of the angle
    cos_theta = math.cos(angle_radians)
    sin_theta = math.sin(angle_radians)

    # Apply the rotation
    x_rotated = x * cos_theta - y * sin_theta
    y_rotated = x * sin_theta + y * cos_theta

    # Return the rotated point as a tuple
    return (round(x_rotated, 5), round(y_rotated, 5))

def gerber_rotate_90(self):
    '''
    Rotate the gerber file (for DIP components)

    Procedure:
    Step-1: switch x and y coordinates
    Step-2: recenter to (x_min, y_min) (which is measured before step 1!!) 
    Done :D

    '''
    # Get X and Y, min for step2 and switching them
    bounds = self.bounds
    x_min = bounds[0][0]
    y_min = bounds[1][0]

    # Step 1: invert x and y coordinates
    # Step 1a: for .statements
    for stmt in self.statements:
        if hasattr(stmt, 'x') and hasattr(stmt, 'y'):
            if type(stmt.x) in [int, float] and type(stmt.y) in [int, float]:
                new_stmt_point = rotate_point((stmt.x, stmt.y), 90)
                stmt.x = new_stmt_point[0]
                stmt.y = new_stmt_point[1]

        elif hasattr(stmt, 'modifiers'):
            if len(stmt.modifiers[0]) > 1:
                stmt.modifiers[0] = (stmt.modifiers[0][1], stmt.modifiers[0][0])

        #TODO: does start and end angle of gerber.primitives.Arc need rotating?!?


    # Step1b: for .primitives
    for ind, primitive in enumerate(self.primitives):
        if type(primitive) == gerber.primitives.Line:
            self.primitives[ind].start = rotate_point(primitive.start, 90)
            self.primitives[ind].end = rotate_point(primitive.end, 90)

        elif type(primitive) == gerber.primitives.Region:
            for ind2, region_primitive in enumerate(primitive.primitives):
                if type(region_primitive) == gerber.primitives.Line:
                    self.primitives[ind].primitives[ind2].start = rotate_point(region_primitive.start, 90)
                    self.primitives[ind].primitives[ind2].end = rotate_point(region_primitive.end, 90)

                else:
                    # Assuming all primitives inside Region object is line
                    raise NotImplementedError("I thought all primitives inside a Region object is Line primitives only")

        elif type(primitive) == gerber.primitives.Arc:
            offset = rotate_point(primitive.center, 90)
            primitive.offset(-primitive.center[0]+offset[0], -primitive.center[1]+offset[1])

        elif type(primitive) == gerber.primitives.AMGroup and primitive.stmt.name == 'RoundRect':

            self.primitives[ind].position = rotate_point(primitive.position, 90)

            for ind2, sub_primitive in enumerate(primitive.primitives):
                if type(sub_primitive) == gerber.rs274x.Outline:
                    for ind3, l in enumerate(sub_primitive.primitives):

                        if type(l) != gerber.primitives.Line:
                            raise NotImplementedError("I thought Outline only contains Line object ;(")

                        if l.aperture.diameter != 0:
                            raise NotImplementedError("I thought outline gerber.primitives.Line objects don't have a thickness ;(")

                        self.primitives[ind].primitives[ind2].primitives[ind3].start = rotate_point(l.start, 90)
                        self.primitives[ind].primitives[ind2].primitives[ind3].end = rotate_point(l.end, 90)

                elif type(sub_primitive) == gerber.rs274x.Circle:
                    self.primitives[ind].primitives[ind2].position = rotate_point(sub_primitive.position, 90)

                else:
                    raise NotImplementedError(f"I thought AMGroup Object named 'RoundRect' in .stmt will only have primitive Outline and Cirle in their primitives list, found {primitive}")


        else:
            # Check if this Gerber type is implemented
            try:
                tmp = GerberToShapely(primitive)
            except NotImplementedError:
                print(f"\nThis Gerber Object {type(primitive)} isn't implemented how to recenter!\n\n")
                raise

            self.primitives[ind].position = rotate_point(primitive.position, 90)
            
            # must invert height and width when rotating 90 degrees
            if hasattr(primitive, 'width') and hasattr(primitive, 'height'):
                self.primitives[ind].width, self.primitives[ind].height = primitive.height, primitive.width

    ### Step 2: recenter to original position
    self.recenter_gerber_file(x_min, y_min)


gerber.rs274x.GerberFile.rotate_90 = gerber_rotate_90

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
        ### DETECTING ROUND RECT AMGroup CORNERCASE
        if object_to_convert.stmt.name == 'RoundRect':
            return GerberToShapely.to_round_rectangle(object_to_convert)

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
        ### Step1: Extracting Arc information from gerber object
        center = object_to_convert.center  # Center of the arc
        radius = object_to_convert.radius  # Radius to the middle of the thickness
        thickness = object_to_convert.aperture.diameter  # Thickness of the arc

        start_angle = object_to_convert.start_angle  # Start angle in degrees
        end_angle = object_to_convert.end_angle # End angle in degrees
        clockwise = False if object_to_convert.direction == 'counterclockwise' else True # Direction of the arc
        num_points = 50  # the resolution of the arc

        if clockwise:
            if start_angle > end_angle:
                pass
            else:
                pass
            raise NotImplementedError("")

        else:
            if start_angle < end_angle:
                angle_offset = 0
            else:
                angle_offset = math.pi

        ### Step2: Creating a shapely Polygon Object
        radius_in = radius - thickness/2
        arc_coords_in = [ (center[0] + radius_in * np.cos(angle+angle_offset), center[1] + radius_in * np.sin(angle+angle_offset)) for angle in np.linspace(start_angle, end_angle, num_points)]

        radius_out = radius + thickness/2
        arc_coords_out = [ (center[0] + radius_out * np.cos(angle+angle_offset), center[1] + radius_out * np.sin(angle+angle_offset)) for angle in np.linspace(start_angle, end_angle, num_points)]

        if clockwise:
            arc_coords_out = arc_coords_out[::-1]
        else:
            arc_coords_in = arc_coords_in[::-1]
        
        polygon_points = arc_coords_in
        polygon_points.extend(arc_coords_out)

        polygon = Polygon(polygon_points)

        return polygon
    
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
                raise NotImplementedError("I thought Outline only contains Line object ;(")

            if shape.aperture.diameter != 0:
                raise NotImplementedError("I thought outline gerber.primitives.Line objects don't have a thickness ;(")

        coord_list = []
        for line in object_to_convert.primitives:
            coord_list.append(line.start)
            coord_list.append(line.end)


        return Polygon(LinearRing(coord_list))

    @classmethod
    def to_polygon(cls, object_to_convert: gerber.primitives.Primitive) -> LinearRing:
        '''

        '''
        return Polygon(LinearRing(object_to_convert.vertices))

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

        region_primitive = object_to_convert.primitives[0]
        if type(region_primitive) == gerber.primitives.Line:
            coord_list = [(region_primitive.start[0], region_primitive.start[1])]
        else:
            # Assuming all primitives inside Region object is Gerber Line object
            raise NotImplementedError("I thought all primitives inside a Region object is Line primitives only")

        for ind, region_primitive in enumerate(object_to_convert.primitives[1:]):
            if type(region_primitive) == gerber.primitives.Line:


                # Checking for discontiniouty errors
                prev_region_primitive = object_to_convert.primitives[ind]
                if not math.isclose(prev_region_primitive.end[0], region_primitive.start[0], rel_tol=1e-5) or not math.isclose(prev_region_primitive.end[1], region_primitive.start[1], rel_tol=1e-5):
                    raise ValueError("Discontinuoty Error")

                # Appending the start of each line
                coord_list.append((region_primitive.start[0], region_primitive.start[1]))

            else:
                # Assuming all primitives inside Region object is Gerber Line object
                raise NotImplementedError("I thought all primitives inside a Region object is Line primitives only")

        return Polygon(LineString(coord_list))

    @classmethod
    def to_round_butterfly(cls, object_to_convert: gerber.primitives.Primitive) -> LinearRing:
        '''

        '''
        raise NotImplementedError("RoundButterfly primitive gerber object convertion to Shapely method still not implemented")

    @classmethod
    def to_round_rectangle(cls, object_to_convert: gerber.primitives.Primitive) -> LinearRing:
        '''

        '''
        if type(object_to_convert) == gerber.rs274x.AMGroup and object_to_convert.stmt.name == 'RoundRect':
            
            ### Step 1: assuming the .primitives of this stupid AMGroup is Outline and Circle, now extracting all lines and the diameter of the 
            lines = []
            corner_diameter = -1
            for primitive in object_to_convert.primitives:
                if type(primitive) == gerber.rs274x.Outline:
                    for l in primitive.primitives:

                        if type(l) != gerber.primitives.Line:
                            raise NotImplementedError("I thought Outline only contains Line object ;(")

                        if l.aperture.diameter != 0:
                            raise NotImplementedError("I thought outline gerber.primitives.Line objects don't have a thickness ;(")

                        lines.append(GerberToShapely(l))

                elif type(primitive) == gerber.rs274x.Circle:
                    corner_diameter = primitive.diameter

                else:
                    raise NotImplementedError("I thought AMGroup Object named 'RoundRect' in .stmt will only have primitive Outline and Cirle in their primitives list")
            else:
                if corner_diameter == -1:
                    raise NotImplementedError("didn't find any Circle objects in this AMGroup named 'RoundRect' in .stmt, thus don't know the diameter of the corners!")

            ### Step 2: find which of the lines represent the height and which represent the width
            is_height = lambda line: line.coords[0][0] == line.coords[1][0]
            is_width = lambda line: line.coords[0][1] == line.coords[1][1]
            heights = []
            widths = []
            for line in lines:
                if is_height(line) and not is_width(line):
                    heights.append(line.length)
                if not is_height(line) and is_width(line):
                    widths.append(line.length)

            #TODO: now that I have extracted the height lines and width lines, I DON'T KNOW which line is the correct width/height
            # for now I just choose the biggest number ;/
            height = max(heights)
            width = max(widths)

            center = object_to_convert.position

            ### Step 3: now that I have the height, width and rounded corner I can construct the rounded rectangle object easily
            # Ensure the corner radius is not greater than half the width or height
            corner_radius = min((corner_diameter/2), width / 2, height / 2)

            # Create the corner arcs
            # Each corner arc is defined by a sequence of points
            def generate_arc(corner_radius, start_angle, end_angle, center=(0, 0), num_points=10):
                """Generate points for an arc centered at a specified point."""
                return [
                    (center[0] + corner_radius * np.cos(angle), center[1] + corner_radius * np.sin(angle))
                    for angle in np.linspace(start_angle, end_angle, num_points)
                    ][::-1]
            
            # Calculate corner centers
            top_left = (center[0] - width / 2 + corner_radius, center[1] + height / 2 - corner_radius)
            top_right = (center[0] + width / 2 - corner_radius, center[1] + height / 2 - corner_radius)
            bottom_right = (center[0] + width / 2 - corner_radius, center[1] - height / 2 + corner_radius)
            bottom_left = (center[0] - width / 2 + corner_radius, center[1] - height / 2 + corner_radius)
    
            # Generate the arcs for the four corners
            arcs = [
                generate_arc(corner_radius, np.pi/2, np.pi, top_left),  # Top-left corner
                generate_arc(corner_radius, 0, np.pi/2, top_right),  # Top-right corner
                generate_arc(corner_radius, 3*np.pi/2, 2*np.pi, bottom_right),  # Bottom-right corner
                generate_arc(corner_radius, np.pi, 3*np.pi/2, bottom_left)  # Bottom-left corner
            ]

            
            # Create straight lines between the arcs
            lines = [
                    [arcs[0][-1], arcs[1][0]],
                    [arcs[1][-1], arcs[2][0]],
                    [arcs[2][-1], arcs[3][0]],
                    [arcs[3][-1], arcs[0][0]]
                ]
           
            # Combine arcs and lines into a single sequence of points
            exterior_points = []
            for i in range(4):
                exterior_points.extend(arcs[i])

                exterior_points.extend(lines[i])
            
            # Create and return the polygon
            return Polygon(exterior_points)

        else:
            raise NotImplementedError("still didn't implement a gerber round rect object only an AMGroup named RoundRect in .stmt")

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

def _turtle_move_trace(turtle, coord_list, x_offset, y_offset, multiplier):
    '''

    '''
    if coord_list:
        turtle.up()
        turtle.setpos((coord_list[0][0] - x_offset) * multiplier, (coord_list[0][1] - y_offset) * multiplier)
        turtle.down()
        for coord in coord_list[1:-1]:
            turtle.setpos((coord[0] - x_offset) * multiplier, (coord[1] - y_offset) * multiplier)

        turtle.setpos((coord_list[-1][0] - x_offset) * multiplier, (coord_list[-1][1] - y_offset) * multiplier)

    else:
        print("Given Empty Coord list to simulate ?!?!")
        raise ValueError("Given Empty Coord list to simulate ?!?!")

def visualize(shape_to_sim: LineString | LinearRing | Polygon | list[Point], hide_turtle=True, speed=0, x_offset=40, y_offset=20, line_width=1.5, multiplier=8, terminate=False) -> None:
    '''
    visualizes the shape object
    '''

    # Set up the turtle screen
    screen = turtle.Screen()
    screen.setup(width=DEVICE_W, height=DEVICE_H, startx=START_X, starty=START_Y)

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
    if type(shape_to_sim) == Polygon:
        coord_list_exterior = list(shape_to_sim.exterior.coords)
        coord_list_list_interiors = list(shape_to_sim.interiors)

        _turtle_move_trace(turtle, coord_list_exterior, x_offset, y_offset, multiplier)
        for coord_list_interior in coord_list_list_interiors:
            _turtle_move_trace(turtle, list(coord_list_interior.coords), x_offset, y_offset, multiplier)

    elif type(shape_to_sim) in [LineString, LinearRing]:
        coord_list = list(shape_to_sim.coords)
        _turtle_move_trace(turtle, coord_list, x_offset, y_offset, multiplier)

    elif all((type(val) == Point) for val in shape_to_sim):
        coord_list = shape_to_sim
        _turtle_move_trace(turtle, coord_list, x_offset, y_offset, multiplier)

    else:
        raise ValueError(f"<shape_to_sim> argument must be of type shapely LineString or LinearRing or Polygon or list[Point]\nGiven type is {type(shape_to_sim)}")

    # Graph.used_colors.add(color)
    # if len(Graph.used_colors) == len(colors):
    #     print('\n\n!!!!!!!!!! COLORS RESET !!!!!!!!!!!!!!!!!\n\n')
    #     Graph.used_colors = set()

    if terminate:
        turtle.done()

def visualize_group(group, gbr_obj=None):
    '''
    visualizes a group of LineString or LinearRing
    '''
    # Calculating Offset by finding center to draw PCB in the center
    if gbr_obj:
        x_center = 2 + (gbr_obj.size[0]//2)
        y_center = 2 + (gbr_obj.size[1]//2)

    else:
        x_center = 0
        y_center = 0

    # Calculating Multiplier
    # multiplier = (DEVICE_W/gbr_obj.size[0]) if (gbr_obj.size[0] > gbr_obj.size[1]) else (DEVICE_H/gbr_obj.size[1])
    # multiplier /= 2
    # multiplier = 50
    multiplier = 5

    len_group = len(group)
    num = 0  # if only one object in the group
    for num, sth in enumerate(group[:-1]):
        print(f"Visualizaing Trace number: {num+1} out of {len_group}")
        visualize(sth, x_offset=x_center, y_offset=y_center, multiplier=multiplier)

    print(f"Visualizaing Trace number: {num+2} out of {len_group}")
    visualize(group[-1], x_offset=x_center, y_offset=y_center, multiplier=multiplier, terminate=True)

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

    # Converting the Gerber Object to Shapely Objects into a dark group and a light group
    shapely_objects_dark = {}
    shapely_objects_clear = {}
    for gerber_primitive in gerber_obj.primitives:
        if gerber_primitive.level_polarity == 'dark':
            shapely_objects_dark[GerberToShapely(gerber_primitive)] = gerber_primitive

        elif gerber_primitive.level_polarity == 'clear':
            shapely_objects_clear[GerberToShapely(gerber_primitive)] = gerber_primitive

        else:
            raise ValueError(f"Unsupported level_polarity: {gerber_primitive.level_polarity}")

    # Subtracting each dark group from all light groups, 
    # (as there is no way to know which shape is supposed to subtract which shape (as far as I know))
    shapely_objects_dark_subtracted = []
    for shapely_obj_d, gbr_obj_d in shapely_objects_dark.items():

        #NOTE: I assume that the only Gerber Objects that have difference operation applied to them by clear objects are 'Region'
        if type(gbr_obj_d) == gerber.rs274x.Region:
            for light_obj in shapely_objects_clear.keys():
                shapely_obj_d = shapely_obj_d.difference(light_obj)

        shapely_objects_dark_subtracted.append(shapely_obj_d)

    # Union all dark group shapes together to form a MultiPolygon Object with all the Polygons that intersect joined
    whole_thing = shapely_objects_dark_subtracted[0]
    for shapely_object in shapely_objects_dark_subtracted[1:]:
        whole_thing = whole_thing.union(shapely_object)
    whole_thing = list(whole_thing.geoms)

    # Getting list of list of extrior coordinate of each Shapley Polygon
    coord_list_list = [list(polygon_.exterior.coords) for polygon_ in whole_thing]
    coord_list_list = [ [ Point( round(coord[0], resolution), round(coord[1], resolution) ) for coord in coord_list ] for coord_list in coord_list_list]

    # Getting list of list of all interiors coordinate lists of each Shapely Polygon
    tmp = [list(interior.coords) for polygon_ in whole_thing for interior in polygon_.interiors]
    tmp = [ [ Point( round(coord[0], resolution), round(coord[1], resolution) ) for coord in tmp_ ] for tmp_ in tmp ]

    # Joinging the exterior and interiors lists of Points
    coord_list_list.extend(tmp)

    if debug:
        visualize_group(coord_list_list, gbr_obj=gerber_obj)

    return coord_list_list

def get_holes_coords(gerber_obj: gerber.rs274x.GerberFile, resolution: int = DEFAULT_RESOLUTION, debug: bool=False) -> list[Point]:
    '''
    Gets list of coordinates where the spindle must go straight down in the Z axis to drill

    :param gerber: Gerber Object from the gerber library
    :param resolution: the number of decimal places for coordinates
    :return: list of holes coordinates
    '''
    coord_list = []
    for primitive in gerber_obj.primitives:

        # Add any position of any Gerber object that is not a Trace; thus a ComponentPad
        if type(primitive) not in [gerber.rs274x.Line, gerber.rs274x.Region]:
            coord_list.append(Point( round(primitive.position[0], resolution), round(primitive.position[1], resolution)))

    if debug:
        print(f"Number of holes to drill: {len(coord_list)}")

    return coord_list

def get_pen_coords(gerber_obj: gerber.rs274x.GerberFile, debug: bool=False) -> list[Point]:
    '''
    '''
    pass

if __name__ == '__main__':
    # gerber_file = 'gerber_files/limit_switch-F_Cu 2.gbr'
    # gerber_file_path = '/home/mr-atom/Projects/PCB_manufacturer/Circuit/limit_switch/Gerber/limit_switch-F_Cu.gbr'
    gerber_file= "gerber_files/region_object.gbr"
    
    gerber_obj = gerber.read(gerber_file)

    print(get_laser_coords(gerber_obj, debug=True))

    
   
