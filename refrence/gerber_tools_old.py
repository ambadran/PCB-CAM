'''
This files contains functions to parse gerber files and deal with them
'''
from __future__ import annotations
from enum import Enum
from dataclasses import dataclass
from typing import Optional
from copy import deepcopy
from Shapely import Point

class ShapeType(Enum):
    Circle = 'C'
    Rectangle = 'R'
    Oval = 'O'


class BlockType(Enum):
    Conductor = 'Conductor'
    ComponentPad = 'ComponentPad'
    Profile = 'Profile'


class Block:
    '''
    Gerber Block of coordinates
    each block is named like this 'Dxx' where xx is the number that identifies this block
    each block has a group type which determines whether it is drill coordinate, trace coordinate or edge coordinates
    each block has a thickness assigned to it
    each block has it's own set of coordinates
    '''
    def __init__(self, D_num: int, coordinates: list[Point], block_type: BlockType, shape_type: ShapeType, 
                    thickness: float, thickness2: Optional[float]=None, 
                    coordinates_with_multiplier: Optional[list[Point]]=None):
        self.D_num = int(D_num)
        self.coordinates = coordinates
        self.block_type = block_type
        self.shape_type = shape_type
        self.thickness = thickness  # Diameter for Circle, length of rectangle?
        self.thickness2 = thickness2
        self.coordinates_with_multiplier = coordinates_with_multiplier

    @classmethod
    def from_gerber(cls, gerber_object: Gerber, block_type: BlockType) -> list[Block]:
        '''
        :param gerber_file: gerber file in string form
        :param block_type: what block type wanted to be extracted from the gerber file

        :returns: a list of ALL Block objects of a specific BlockType found in a gerber file 
        '''
        gerber_file = gerber_object.gerber_file
        g_file_lines = gerber_file.split('\n')

        d_nums: list[ind] = []
        coordinates: dict[int: list[Point]] = {}  # key is index and value is value
        coordinates_with_multiplier: dict[int: list[point]] = {}  # key is index and value is value
        shape_types: list[ShapeType] = []
        thicknesses: list[float] = []
        thicknesses2: list[float] = []
        # getting the Dxx of the block we want and shape types
        to_ShapeType = {shape_type.value: shape_type for shape_type in ShapeType}
        for line_num, line in enumerate(g_file_lines):
            if block_type.value in line:
                wanted_line = g_file_lines[line_num+1]

                # getting the D number of the profile definition, by finding the last char that is a digit
                start_wanted_index = wanted_line.find('%ADD') + 4
                for char_num, char in enumerate(wanted_line[start_wanted_index:]):
                    if not char.isdigit():
                        end_wanted_index = 4 + char_num
                        break
                d_nums.append(wanted_line[start_wanted_index:end_wanted_index])
                coordinates[d_nums[-1]] = []
                coordinates_with_multiplier[d_nums[-1]] = []
                shape_types.append(to_ShapeType[wanted_line[end_wanted_index]])

                if shape_types[-1] == ShapeType.Rectangle or shape_types[-1] == ShapeType.Oval: 
                    # two thickness values; length and width
                    thickness, thickness2 = wanted_line[end_wanted_index+2:wanted_line.index('*')].split('X')
                    thicknesses.append(float(thickness))
                    thicknesses2.append(float(thickness2))

                elif shape_types[-1] == ShapeType.Circle:
                    # one thickness value
                    thicknesses.append(float(wanted_line[end_wanted_index+2:wanted_line.index('*')]))
                    thicknesses2.append(None)


        # getting all the gerber coordinates under the wanted Dxx
        take_lines = False
        g_file_lines_start_ind = gerber_file[:gerber_file.find('D')].count('\n')  # coordinates start from first 'D' occurance
        for line_num, line in enumerate(g_file_lines[g_file_lines_start_ind:]):

            #TODO: ASSUMPTION!! Here I am assuming start of a block always looks like this 'Dxyz', where x is int, y int or nothing and z is any character
            if line.startswith('D'):  # decide on whether to take lines or not
                current_dnum = line[1:-1]
                take_lines = current_dnum in d_nums
                continue

            if take_lines:
                coordinate_with_multiplier = Gerber.get_XY(line)
                if coordinate_with_multiplier is not None:
                    coordinates_with_multiplier[current_dnum].append(coordinate_with_multiplier)

                    coordinates[current_dnum].append(Point(coordinate_with_multiplier.x / gerber_object.x_multiplier,
                            coordinate_with_multiplier.y / gerber_object.y_multiplier, None, coordinate_with_multiplier.d))

        debug = False
        if debug:
            print(len(d_nums))
            print(len(shape_types))
            print(len(thicknesses))
            print(len(coordinates))
            print(len(coordinates_with_multiplier))
            print(len(thicknesses2))
            print()

            print(d_nums)
            print(shape_types)
            print(thicknesses)
            print(coordinates)
            print(coordinates_with_multiplier)
            print(thicknesses2)
            print()

        blocks = []
        for ind in range(len(d_nums)):
            blocks.append(Block(d_nums[ind], coordinates[d_nums[ind]], block_type, shape_types[ind], 
                            thicknesses[ind], thicknesses2[ind], 
                            coordinates_with_multiplier[d_nums[ind]]))

        return blocks

    def __repr__(self) -> str:
        '''
        repr representatin
        '''
        return f"D{self.D_num} of shape {self.shape_type}"

    def __str__(self) -> str:
        '''
        string representation
        '''
        thickness2_str =  "" if self.thickness2 is None else f"x{self.thickness2}"
        return f"D{self.D_num} of shape {self.shape_type}, thickness {self.thickness}{thickness2_str} and {len(self.coordinates)} coordinates"


class Gerber:
    '''
    Class to implement basic functionlity to read, manipulate and write gerber files
    '''
    def __init__(self, *arg, file_path: str=None, file_content: str=None):
        '''
        Initializing the Gerber object!
        '''
        if file_path == None and file_content == None or (type(file_path) == str and type(file_content) == str):
            raise ValueError("Must pass only one of file_path or file_content parameters")

        if type(file_path) not in [str, type(None)] or type(file_content) not in [str, type(None)]:
            raise ValueError('Must only pass String or not')

        if file_path:
            self.gerber_file = self.read_gerber_file(file_path)

        elif file_content:
            self.gerber_file = file_content

        else:
            raise ValueError("HOWWW ;;;;;(")

        self.x_multiplier, self.y_multiplier = self.get_x_y_multiplier()

        self.blocks: dict[BlockType: list[Block]] = {

                        BlockType.Profile: Block.from_gerber(self, BlockType.Profile), 

                        BlockType.Conductor: Block.from_gerber(self, BlockType.Conductor),

                        BlockType.ComponentPad: Block.from_gerber(self, BlockType.ComponentPad)
                }

        self.coordinates: dict[BlockType: list[Point]] = {

            BlockType.Profile:
                [coordinate for block in self.blocks[BlockType.Profile] for coordinate in block.coordinates],

            BlockType.Conductor:
                [coordinate for block in self.blocks[BlockType.Conductor] for coordinate in block.coordinates],

            BlockType.ComponentPad:
                [coordinate for block in self.blocks[BlockType.ComponentPad] for coordinate in block.coordinates],
        }

        self.coordinates_with_multiplier: dict[BlockType: list[Point]] = {

            BlockType.Profile:
                [coordinate for block in self.blocks[BlockType.Profile] for coordinate in block.coordinates_with_multiplier],

            BlockType.Conductor:
                [coordinate for block in self.blocks[BlockType.Conductor] for coordinate in block.coordinates_with_multiplier],

            BlockType.ComponentPad:
                [coordinate for block in self.blocks[BlockType.ComponentPad] for coordinate in block.coordinates_with_multiplier],
        }

    def read_gerber_file(self, file_path: str) -> str:
        '''
        :param file_path: path to a gerber file
        reads the gerber file checks if it's a gerber file
        then returns it
        '''
        with open(file_path) as g_file:
            gerber_file = g_file.read() 

        self.check_GerberFile()

        return gerber_file

    def check_GerberFile(self) -> None:
        '''
        raises error if it's not a gerber file
        '''
        pass

    def create_gerber_file(self, gerber_file_name: str) -> None:
        """
        This function just writes the string input gerber file content to a <file_name>.gbr
        :gerber_file_name: name of the file to be created/overwritten
        """
        gerber_file = self.gerber_file
        self.check_GerberFile()

        with open(gerber_file_name, 'w') as g_file:
            g_file.write(gerber_file)

    @classmethod
    def get_XY(cls, line: str) -> Point:
        '''
        :param line: line string from gerber file
        :return: a Point object
        '''

        if not line.startswith('X'):
            return None

        try:
            x = int(line[1 : line.index('Y')])
        except ValueError:  # it's a float not an integer 
            x = float(line[1 : line.index('Y')])

        try:
            y = int(line[line.index('Y')+1 : line.index('D')])
        except ValueError:  # it's a float not an integer
            y = float(line[line.index('Y')+1 : line.index('D')])

        d = int(line[line.index('D')+1 : line.index('*')])

        return Point(x, y, None, d)

    def generate_line(self, line: str, coordinate: Coordinate) -> str:
        '''
        :param line: the old line, #NOTE: it's wanted to get the D value at the end of each gerber coordinate line
        :param coordinates: list of x value and y value
        :return: line string with update coordinates values
        '''
        # Make sure it's indeed a coorindate gerber line
        if not line.startswith('X'):
            raise ValueError("the input line doesn't start with X. This is not a coordinate line.")

        if type(coordinate.x)!= int or type(coordinate.y) != int:
            raise ValueError("Coordinates to be written to gerber file MUST be integers NOT floats")
        
        # Get Index of x coordinate value and y coordinate value
        D_value = line[line.index('D'):]

        # Creating the new line 
        new_line = f"X{str(coordinate.x)}Y{str(coordinate.y)}{D_value}"

        return new_line

    def get_x_y_multiplier(self) -> tuple[int, int]:
        '''
        gerber files has coordinates in mm * 10**6 or even 8, this function return the multipler, e.g- the 10**6 

        :return: two integers one for the x multipler and the other for the y multiplier
        '''
        gerber_file = self.gerber_file

        start_ind = gerber_file.index("%FSLA") + 5
        end_ind = start_ind + gerber_file[start_ind:].index('\n')

        percision_set_line = gerber_file[start_ind:end_ind]

        ger_percision_x_format = int(percision_set_line[1 : percision_set_line.index('Y')])
        ger_percision_y_format = int(percision_set_line[percision_set_line.index('Y')+1 : percision_set_line.index('*')])

        if ger_percision_x_format == 46:
            x_multiplier = 10**6
        else:
            raise ValueError("unknown percision x format in line that contain '%FSLA'")

        if ger_percision_y_format == 46:
            y_multiplier = 10**6
        else:
            raise ValueError("unknown percision y format in line that contain '%FSLA'")

        return x_multiplier, y_multiplier

    def apply_multiplier(self, coordinate: Coordinate) -> Coordinate:
        '''
        applies to gerber multiplier to a list of coordinates
            e.g: 1.36 -> 1360000000

        :param coordinate: coordinates to apply multiplier to
        :return: coordinate with applied multiplier
        '''
        return Coordinate(int(coordinate.x * self.x_multiplier), int(coordinate.y * self.y_multiplier))

    @staticmethod
    def recenter_gerber_file(self, x_offset: int, y_offset: int) -> None:
        '''
        self.gerber_file is recentered according to input offsets

        :param x_offset: wanted x offset from origin. if 0 then pcb will start at 0
        :param y_offset: wanted y offset from origin. if 0 then pcb will start at 0
        '''

        # Get the all coordinates that relate to the Edge of the PCB
        coordinates = self.coordinates_with_multiplier[BlockType.Profile]

        # Get X and Y, min and max
        min_coordinate, max_coordinate = Coordinate.get_min_max(coordinates)
        x_min = min_coordinate.x
        y_min = min_coordinate.y

        # Calculating the offset to be added to each coordinate in the gerber file
        x_offset = int(-x_min + x_offset * self.x_multiplier)
        y_offset = int(-y_min + y_offset * self.y_multiplier)

        # Generating the new gerber file with the offset added to every line of coordinates
        g_file_lines = self.gerber_file.split('\n')
        for line_num, line in enumerate(g_file_lines):

            coordinates = Gerber.get_XY(line)
            if coordinates:
                coordinates.x += x_offset
                coordinates.y += y_offset

                g_file_lines[line_num] = self.generate_line(line, coordinates)

        new_file = "\n".join(g_file_lines)

        self = Gerber(file_content=new_file)
        return self

    def blocks_to_graph(self, blocks: list[Block]) -> Graph:
        '''
        creates a graph data structure from the given block objects

        :param block: Block objects to convert their coordinates to a graph
        :return: graph data structure of given blocks coordinates
        '''
        all_traces = Graph()

        edge_start_available = False
        edge_end_available = False
        encountered_one_edge_start = False

        for block in blocks:
            for coord in block.coordinates:
                if coord not in all_traces:
                    all_traces.add_vertex(coord)

                if coord.d == 2: #  edge start coordinate
                    edge_start = coord
                    edge_start_available = True
                elif coord.d == 1:  # edge end coordinate
                    edge_end = coord
                    edge_end_available = True
                    encountered_one_edge_start = False
                else:
                    raise ValueError("Never seen this before!!")

                if edge_start_available and encountered_one_edge_start:
                    raise ValueError("TWO consecutive start coordinates")

                if not edge_start_available and edge_end_available:
                    raise ValueError("End coordinate then start coordinate")
                elif edge_start_available and edge_end_available:
                    all_traces.add_edge(Edge(edge_start, edge_end, block.thickness))
                    edge_start_available = False
                    edge_end_available = False
                elif edge_start_available and not edge_end_available:
                    encountered_one_edge_start = True
                else:
                    raise ValueError("HOW THE FUCK DID IT END UP HERE?!?!?!?!!")
                    
                    
        return all_traces

    def mirror(self, x_y_axis: bool=True) -> None:
        '''
        :param x_y_axis: determines whether to mirror in x or y axis, default is x-axis mirroring
        Mirrors the gerber file for backward etching
        '''
        #TODO: check if it's only one layer PCB first,
        # if not then raise Error

        # Get the all coordinates that relate to the Edge of the PCB
        coordinates = self.coordinates_with_multiplier[BlockType.Profile]

        # Get X and Y, min and max
        min_coordinate, max_coordinate = Coordinate.get_min_max(coordinates)
        # min coords are the current offsets as well
        x_min = min_coordinate.x
        y_min = min_coordinate.y

        # mirroring the file
        g_file_lines = self.gerber_file.split('\n')
        for line_num, line in enumerate(g_file_lines):

            coordinates = Gerber.get_XY(line)
            if coordinates:
                if x_y_axis:
                    coordinates.x *= -1  # mirroring
                else:
                    coordinates.y *= -1  # mirroring

                g_file_lines[line_num] = self.generate_line(line, coordinates)


        new_file = "\n".join(g_file_lines)
        self = Gerber(file_content=new_file)

        # applying old offsets
        x_min_offset = round(x_min/self.x_multiplier, 6)
        y_min_offset = round(y_min/self.y_multiplier, 6)
        self = Gerber.recenter_gerber_file(self, x_min_offset, y_min_offset)

        return self


if __name__ == '__main__':

    # gerber_file_path = 'gerber_files/test.gbr'
    # gerber_file_path = '/home/mr-atom/circuit_projects/current_sensor/current_sensor/Gerber/current_sensor-F_Cu.gbr'
    # gerber_file_path = '/Users/ambadran717/circuit_projects/unipolar_driver V2/Circuit/Circuit/Gerber/unipolar stepper driver-F_Cu.gbr'
    gerber_file_path = '/Users/ambadran717/circuit_projects/current-sensor V1/current_sensor/Gerber/current_sensor-F_Cu.gbr'
    # gerber_file_path = '/home/mr-atom/Projects/PCB_manufacturer/Circuit/limit_switch/Gerber/limit_switch-F_Cu.gbr'
    # gerber_file_path = '/home/mr-atom/Projects/PCB_manufacturer/Circuit/DC_Motor_Driver/Gerber/DC_Motor_Driver-F_Cu.gbr'


    # new_file_name = '/Users/ambadran717/circuit_projects/unipolar_driver V2/Circuit/Circuit/Gerber/mirrored_offseted.gbr'
    new_file_name = '/Users/ambadran717/circuit_projects/current-sensor V1/current_sensor/Gerber/mirrored_offseted.gbr'
    # new_file_name= '/home/mr-atom/Projects/PCB_manufacturer/Circuit/limit_switch/Gerber/mirrored_offseted.gbr'
    # new_file_name= '/home/mr-atom/Projects/PCB_manufacturer/Circuit/DC_Motor_Driver/Gerber/mirrored_offseted.gbr'

    # Offset PCB from (0, 0)
    x_offset = 2
    y_offset = 2

    # Initializing GerberFile Object
    gerber_object = Gerber(file_path=gerber_file_path)

    # Mirroring the Gerber file
    gerber_object = gerber_object.mirror()

    # Recenter Gerber File with wanted Offset
    gerber_object = Gerber.recenter_gerber_file(gerber_object, x_offset, y_offset)
    
    # Writing a new gerber file for current gerber file content
    gerber_object.create_gerber_file(new_file_name)


