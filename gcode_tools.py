'''
This file has function to generate the gcode we want
'''
from enum import Enum
from typing import Callable, Optional
from math import floor, ceil
import re
from contextlib import contextmanager
import serial
from dataclasses import dataclass
import json
import warnings
with warnings.catch_warnings():
    # suppressing a stupid syntax warning to convert 'is not' to '!='
    warnings.filterwarnings("ignore", category=SyntaxWarning)
    import gerber
from cam import get_traces_outlines, get_holes_coords, get_pen_coords, Point

def get_max_decimal_place(value: float) -> int:
    '''
    finds out how much decimal places does the number has

    :param value: the value to be tested for how much decimal places
    :returns: the number of decimal places of parameter value
    '''
    num_dec_places = 0
    while round(value, num_dec_places) != value:
        num_dec_places += 1

    return num_dec_places


def increment_current_decimal_point(value: float, current_decimal_points: int, max_dec_places: int=5) -> float:
    '''
    increment the argument value in the wanted current_decimal_points decimal value

    :param value: value to be incremented
    :param current_decimal_points: which decimal place to increment the value
    :param max_dec_places: maximum decimal points to return

    :return: incremented value in the wanted decimal place
    '''
    num_to_increment = 10**-current_decimal_points
    return_value = round(value+num_to_increment, max_dec_places)
    return return_value


class UnitMode(Enum):
    INCH = 20
    MM = 21

class DistanceMode(Enum):
    ABSOLUTE = 90
    INCREMENTAL = 91

class MotionMode(Enum):
    RAPID = 0
    USE_FEEDRATE = 1
    CIRCULAR_CW = 2
    CIRCULAR_CCW = 3
    PROBE_TOWARD_ERROR = 38.2
    PROBE_TOWARD_NO_ERROR = 38.3
    PROBE_AWAY_ERROR = 38.4
    PROBE_AWAY_NO_ERROR = 38.5
    NO_MODE = 80

class FeedRateMode(Enum):
    ONE_PER_MINUTE = 93
    UNIT_PER_MIN = 94

class PlaneSelect(Enum):
    XY = 17
    XZ = 18
    YZ = 19

class ProgramMode(Enum): 
    PROGRAM_STOP = 0
    OPTIONAL_PROGRAM_STOP = 1
    PROGRAM_END = 2
    PROGRAM_END_REWIND = 30

class SpindleState(Enum):
    ON_CW = 3
    ON_CCW = 4
    OFF = 5

class CoolantState(Enum):
    FLOOD = 7
    MIST = 8
    FLOOD_MIST_OFF = 9

ALL_OPTION_GROUPS = {UnitMode: "G", 
        DistanceMode: "G", 
        MotionMode: "G", 
        FeedRateMode: "G", 
        PlaneSelect: "G", 
        ProgramMode: "M", 
        SpindleState: "M", 
        CoolantState: "M"}

non_modal_options = {'feedrate': 'F', 
                     'spindle_speed': 'S',
                     'tool': 'T',
                     'comment': '  ; '}

class ToolChange(Enum):
    Deselect = 0
    Select = 1

class Tool(Enum):
    Empty = 0
    Laser = 1
    Spindle = 2
    Pen = 3


def get_coordinate_from_kwargs(kwargs) -> str:
    '''
    reads the kwargs argument and return something like X_Y_ for gcode usage

    :param kwargs: must input either coordinate=[x, y] or one of x=int, y=int, z=int or a combination of those three
    :return: gcode coordinate string
    '''
    gcode = ''

    coordinate_mode = False
    letter_mode = False

    for key, value in kwargs.items():

        if key == 'coordinate':
            if letter_mode:
                raise ValueError("Can't have both coordinate argument and x, y or z arguments")
            coordinate_mode = True

            if type(value) != Point:
                raise ValueError(f"type {type(value)} is passed! Value must be of type Point")

            if not value.has_z:
                try: # checking internal values are numbers
                    tmp = float(value[0])
                    tmp = float(value[1])
                except Exception:
                    raise ValueError(f"Point list must only contain integers or floats, passed type is {type(value[0])}, {type(value[1])}")

                x_val = value[0]
                if type(x_val) == float:
                    x_val = round(x_val, 3)

                y_val = value[1]
                if type(y_val) == float:
                    y_val = round(y_val, 3)

                gcode += f'X{x_val}Y{y_val}'

            else:
                try: # checking internal values are numbers
                    tmp = float(value[0])
                    tmp = float(value[1])
                    tmp = float(value[2])
                except Exception:
                    raise ValueError(f"Point list must only contain integers or floats, passed type is {type(value[0])}, {type(value[1])}, {type(value[2])}")

                x_val = value[0]
                if type(x_val) == float:
                    x_val = round(x_val, 3)

                y_val = value[1]
                if type(y_val) == float:
                    y_val = round(y_val, 3)

                z_val = value[2]
                if type(z_val) == float:
                    z_val = round(z_val, 3)

                gcode += f'X{x_val}Y{y_val}Z{z_val}'



        elif key == 'x' or key == 'X':
            if coordinate_mode:
                raise ValueError("Can't have both coordinate argument and x, y or z arguments")
            letter_mode = True

            if not(type(value) == int or type(value) == float):
                raise ValueError('X value must be an integer or float')

            x_val = value
            if type(x_val) == float:
                x_val = round(x_val, 3)
            gcode += f'X{x_val}'

        elif key == 'y' or key == 'Y':
            if coordinate_mode:
                raise ValueError("Can't have both coordinate argument and x, y or z arguments")
            letter_mode = True 

            if not(type(value) == int or type(value) == float):
                raise ValueError('Y value must be an integer or float')

            y_val = value
            if type(y_val) == float:
                y_val = round(y_val, 3)
            gcode += f'Y{y_val}'

        elif key == 'z' or key == 'Z':
            if coordinate_mode:
                raise ValueError("Can't have both coordinate argument and x, y or z arguments")
            letter_mode = True 

            if not(type(value) == int or type(value) == float):
                raise ValueError('Z value must be an integer or float')

            z_val = value
            if type(z_val) == float:
                z_val = round(z_val, 3)
            gcode += f'Z{z_val}'

        else:
            raise ValueError("Unknown keyword argument! Supported keywords: coordinate, x, y, z")

    return gcode

#TODO: Implement set_coordinate_system properly

# def set_grbl_coordinate(distance_mode: DistanceMode, comment: Optional[str]=None, **coordinate) -> str:
#     '''
#     overwrites the current grbl working coordinate
#     :param kwargs: must input either coordinate=[x, y] or one of x=int, y=int, z=int or a combination of those three

#     :return: gcode line of the wanted inputs
#     '''
#     comment_available = False

#     if distance_mode == DistanceMode.ABSOLUTE:
#         gcode = "G10 P0 L20 "
#     elif distance_mode == DistanceMode.INCREMENTAL:
#         gcode = '#TODO '
#     else:
#         raise ValueError("Unsupported Mode!")

#     gcode += get_coordinate_from_kwargs(coordinate)

#     if comment:
#         gcode += f" ; {comment}"

#     gcode += '\n'

#     return gcode


def general_machine_init() -> str:
    '''
    Normal initiation routines to make sure the machine will work fine

    :returns: machine initiation gcode
    '''
    gcode = ''

    # G-Code to be generated
    gcode += '; This gcode is generated by my specialised python script for my PCB manufacturer project :))\n'

    # gcode += '; Machine Initialization Sequence...\n\n'

    # M5 disables spindle PWM, C0 chooses empty tool slot in multiplexer, to ensure no endeffector works by mistake 
    # gcode += f'M5 ; disabling spindle PWM\n'
    # gcode += f'C0 ; Choosing the empty tool slot in the multiplexer circuits\n\n'

    # Turn ON Machine
    # gcode += f"B1 ; Turn ON Machine\n\n"

    # HOMING, machine is at (0, 0, 0) now
    # gcode += f"$H ; Homing :)\n"

    # Make sure grbl understands it's at zero now
    # gcode += set_grbl_coordinate(DistanceMode.ABSOLUTE,
    #         comment="Force Reset current coordinates after homing\n", 
    #         coordinate=Point(0, 0, 0))
    
    return gcode


def general_machine_deinit() -> str:
    '''
    Normal Deinitiation routine

    :return: machine deninitiation gcode
    '''
    gcode = ''
    gcode += '; Machine deinitialization Sequence... \n'
    gcode += move(MotionMode.RAPID, coordinate=Point(0, 0, 2))
    # gcode += 'B0 ; Turn Machine OFF\n'

    return gcode

def set_modal_options(*options, comment: str="", return_after: bool=True) -> str:
    '''
    motion Mode
    distance Mode
    unit Mode
    plane select
    feedrate Mode
    program Mode
    spindle state
    coolant state
    '''
    global ALL_OPTION_GROUPS

    gcode = ""

    processed_options = set()
    processed_modal_groups = set() 
    for option in options:
        for option_group, command_keyword in ALL_OPTION_GROUPS.items():
            if option in option_group._member_map_.values():

                if option_group in processed_modal_groups:
                    raise ValueError("Can't pass two options of the same Modal Group")

                processed_modal_groups.add(option_group)
                processed_options.add(option)

                gcode += f"{command_keyword}{option.value}"

    if processed_options != set(options):
        raise ValueError(f"Unknown Options Given!\nargs: {options}\nprocessed_options: {processed_options}")

    if comment:
        gcode += f"  ; {comment}"

    if return_after:
        gcode += '\n'

    return gcode

def set_non_modal_options(**options) -> str:
    '''
    F - feedrate
    S - spindle speed
    T - Tool select
    '''
    global non_modal_options

    gcode = ""
    
    for option, value in options.items():
        if option in non_modal_options.keys():
            gcode += f"{non_modal_options[option]}{value}"

        elif option == 'return_after':
            return_after = options['return_after']

        else:
            raise ValueError(f"Unknown option passed: {option}")

    if 'return_after' in options.keys():
        if return_after:
            gcode += '\n'
    else:
        gcode += '\n' # default is it's there

    return gcode

def move(*modal_options, **non_modal_options_and_coordinates) -> str:
    '''
    generates movement Gxx gcode commands according to inputs

    :param **coordinates: must input either coordinate=[x, y] or one of x=int, y=int, z=int or a combination of those three

    :return: return
    '''
    global non_modal_options

    gcode = ""

    # Modal Options
    if MotionMode not in [type(modal_option) for modal_option in modal_options]:
        gcode += set_modal_options(MotionMode.USE_FEEDRATE, *modal_options, return_after=False)
    gcode += set_modal_options(*modal_options, return_after=False)

    # Seperating coordinate kwargs from non_modal_options kwargs first
    non_modal_options_kwargs = {key: value for key, value in non_modal_options_and_coordinates.items() if key in non_modal_options.keys()}
    coordinates_kwargs = {key: value for key, value in non_modal_options_and_coordinates.items() if key not in non_modal_options_kwargs.keys()}

    # Coordinates
    gcode += get_coordinate_from_kwargs(coordinates_kwargs)

    # Non Modal Options
    gcode += set_non_modal_options(**non_modal_options_kwargs, return_after=False)

    # EOL
    gcode += '\n'
    
    return gcode


def dwell(seconds: int, comment: Optional[str]=None) -> str:
    '''
    returns Gcode to dwell, (sleep for a specific amounts of seconds)
    '''
    return f"G4 P{seconds}  ; {comment}\n"


def get_tool_func(latch_offset_distance_in: int, latch_offset_distance_out: int, tool_home_coordinates: dict[int: tuple[int, int, int]], tool_offsets: dict[int: tuple[int, int, int]], attach_detach_time: int) -> Callable:
    '''
    Closure Function to define constant values for:
    :param latch_offset_distance_in: the distance the male end kinematic mount has to move (+X) to enter female latch
                                     #NOTE this value is INCREMENTAL

    :param latch_offset_distance_out: after the male and female kinematic mount are joined, the distance to move
                                      back to pull the female kinematic mount body off the hanger (-X)
                                      #NOTE this value is INCREMENTAL

    :param tool_home_coordinates: dictionary for each tool, where the value is the coordinate of the home position of the
                                  corresponding tool
                                  #NOTE this value is ABSOLUTE relative to origin (origin is zero when no head is there)

    :param tool_offsets: dictionary for each tool, where the value is the coordinate offset to set the new exact
                         end effector position relative from Origin (0, 0, 0)
                         #NOTE this value is INCREMENTAL 

    :param attach_detach_time: time for kinematic latch to engage or disengage (in ms)!!!

    :returns: the actual tool changing gcode generator function with the proper setup values
    '''
    def tool(tool_change_mode: ToolChange, wanted_tool: Tool) -> str:
        '''
        #NOTE VERY VERY IMPORTANT, THIS FUNCTION ASSUMES TOOL HEAD IS EMPTY!!!
        #NOTE VERY VERY IMPORTANT, THIS FUNCTION ASSUMES THE MACHINE IS HOMED!!!

        Generate Gcode to select/deselect wanted tool
        :param tool_change_mode: select or deselect Mode Enum
        :param wanted_tool: the wanted tool to select/deselect

        :return: gcode to select and activate the tool
        #TODO: implement eeprom tool select memory in microcontroller, read it to know last tool selected
        '''
        gcode = ''
        
        tool_home_coordinate = tool_home_coordinates[wanted_tool.value]
        tool_offset = tool_offsets[wanted_tool.value]

        if tool_change_mode == ToolChange.Select:

            gcode += f"; Getting and Activating Tool-{wanted_tool.value}, The {wanted_tool}\n"

            ### Go get the tool
            # go to tool coordinate but male latch is just outside the female latch
            gcode += move(MotionMode.RAPID, comment=f'Go to Tool-{wanted_tool.value} Home Pos', coordinate=tool_home_coordinate)
            # Now male latch inside female latch, using incremental gcode
            gcode += move(MotionMode.RAPID, comment='Enter Female Kinematic Mount Home Pos', x=latch_offset_distance_in)
            # now male latch twisting and locking on
            gcode += f"A1 ; Latch on Kinematic Mount\n"  
            # Wait until male latch is fully locked on
            gcode += f"G4 P{attach_detach_time} ; Wait for Kinematic Mount to fully attach\n"  
            # now pull off the female kinematch mount off its hanger, using incremental gcode
            gcode += move(MotionMode.RAPID, comment='Exit Female Kinematic Mount Home Pos', x=latch_offset_distance_out)

            ### Fixing Current Point according the new tool head
            gcode += set_grbl_coordinate(DistanceMode.INCREMENTAL, comment=' ;Add tool offset coordinate', coordinate=tool_offset)

            ### Activate it by sending the corresponding tool number in the multiplexer
            gcode += f'C{wanted_tool.value} ; Choosing tool {wanted_tool.value} in the choose demultiplexer circuits\n'

        elif tool_change_mode == ToolChange.Deselect:

            gcode += f"; Returning the Deactivating Tool-{wanted_tool.value}\n"

            ### Selecting empty tool slot in the multiplexer to stop any potential end effector action.
            gcode += 'C0 ; PWM Tool select demultiplexer to select tool zero which is the empty tool slot in multiplexers\n'

            ### Overide current coordinate to go to tool home pos relative to origin by inversing the tool_offset
            tool_offset = Point(tool_offset.x*-1, tool_offset.y*-1, tool_offset.z*-1)
            gcode += set_grbl_coordinate(DistanceMode.INCREMENTAL, comment=' ;Remove tool offset coordinate', coordinate=tool_offset)

            ### Deactivate it by selecting the empty tool in the multiplexer
            # go to tool coordinate but male latch is just outside the female latch
            gcode += move(MotionMode.RAPID, comment=f'Go to Tool-{wanted_tool.value} Home Pos', coordinate=tool_home_coordinate)
            # Put the tool back to it's hanger
            gcode += move(MotionMode.RAPID, comment='Enter Female Kinematic Mount Home Pos', x=latch_offset_distance_out)
            # male latch untwisting from female latch and locking off
            gcode += f"A0 ; Latch OFF Kinematic Mount\n" 
            # Wait until male latch is fully locked off
            gcode += f"G4 P{attach_detach_time} ; Wait for Kinematic Mount to fully detach\n"
            # Now pull off the male kinematic mount away from the female kinematic mount
            gcode += move(MotionMode.RAPID, comment='Exit Female Kinematic Mount Home Pos', x=latch_offset_distance_in)

        else:
            raise ValueError("Mode unknown")

        gcode += '\n'
        return gcode

    return tool


def generate_holes_gcode(gerber_obj: gerber.rs274x.GerberFile, settings) -> str:
    '''
    Takes in String gerber file content, identifies the PCB holes and generates the Gcode to drill the holes from begging to end!

    :param gerber: Gerber object from the gerber library
    :param settings:
    :return: This function creates the gcode content as string according to the input coordinates
    '''
    ### Preparations
    #TODO: fix this line to return the coordinates using the python gerber library. I am still not sure how to extract componentPad coords
    coordinates = get_holes_coords(gerber_obj, debug=settings.debug)

    ### Gcode
    gcode = ''

    gcode += '\n; PCB hole drilling Gcode\n\n'

    #  Starting Spindle and Setting the correct spindle speed
    gcode += set_non_modal_options(spindle_speed=settings.spindle_speed,
            feedrate=settings.spindle_feedrate_Z_hole,
            comment="Settings Non Modal Groups\n")

    # Making sure Modal Group settings are correct
    gcode += set_modal_options(MotionMode.USE_FEEDRATE, 
            DistanceMode.ABSOLUTE, 
            UnitMode.MM, 
            PlaneSelect.XY, 
            FeedRateMode.UNIT_PER_MIN,
            comment="Setting Modal Groups")

    # Starting Spindle Away from surface
    gcode += move(MotionMode.RAPID,
            DistanceMode.ABSOLUTE,
            Z=2,
            comment="Going Up from surface to start spindle")
    gcode += set_modal_options(SpindleState.ON_CW, 
            comment="Spindle ON CW")
    gcode += dwell(settings.spindle_dwell_time, comment="dwell for {settings.spindle_dwell_time} seconds so motor reaches full RPM\n")
    gcode += '\n'

    # Cutting starts here :)
    for coordinate in coordinates:
        gcode += move(MotionMode.RAPID, 
                coordinate=coordinate)
        gcode += move(MotionMode.USE_FEEDRATE,
                z=settings.spindle_Z_down_hole, 
                feedrate=settings.spindle_feedrate_Z_hole)
        gcode += move(MotionMode.RAPID,
                z=settings.spindle_Z_up_position)
    gcode += '\n'

    # deactivating the tool PWM
    gcode += f'M5 ; disabling spindle PWM\n\n'

    # Get the tool back to its place and deselect the tool
    if tool:
        gcode += tool(ToolChange.Deselect, Tool.Spindle)

    return gcode

#def generate_ink_laying_gcode(gerber: gerber.rs274x.GerberFile, tool: Callable, tip_thickness: float, pen_down_position: int, 
#        feedrate: int, debug: bool=False) -> str:
#    '''
#    :param gerber: Gerber Object from the gerber library
#    :param tool: The tool function defined inside the get_tool_func closure function, it generates gcode to select wanted tool
#    :param tip_thickness: number to convey thickness of pen tip in mm
#    :param pen_down_position: position that pen touches PCB in Z axis
#    :param feedrate: integer mm/minute, only for x and y movement for pen movement when drawing

#    :return: This function creates the gcode content as string according to the input coordinates
#    '''
#    ### Working out the variables ###
#    # Get min/max of PCB outline

#    #TODO: use the new python gerber library to return edge coordinates. 
#    #OLD CODE: edge_coordinates = gerber.coordinates[BlockType.Profile]
#    #NEW CODE: edge_coordinates = gerber.bounds #TODO: make the output of this python gerber the same as my old output


#    min_coord, max_coord = Point.get_min_max(edge_coordinates)

#    # Finding num_ys and overlapping_distance
#    #NOTE: Detailed description of what i am doing here is in the iPad notes
#    y_length = round(max_coord.y - min_coord.y, 2)

#    OD_min_value = 1
#    OD_max_value = tip_thickness - 1

#    num_ys_max_value = floor( ( y_length ) / (tip_thickness - OD_max_value) )
#    num_ys_min_value = ceil( ( y_length ) / (tip_thickness - OD_min_value) )
    

#    results = {}  # key is num_ys and value is overlapping_distance
#    for num_ys in range(num_ys_min_value, num_ys_max_value+1):
#        # Equation to find overlapping_distance according to given inputs, mainly the num_ys
#        overlapping_distance_unrounded = (tip_thickness+num_ys*tip_thickness-y_length) / (num_ys + 2)
#        overlapping_distance = round(overlapping_distance_unrounded, 2)
#        results[num_ys] = overlapping_distance

#    num_ys = list(results.keys())[0]  # Choosing the value with least amount of num_ys
#    overlapping_distance = list(results.values())[0]  # Choosing the value with least amount of num_ys
    
#    # Finding the rest of the values
#    x_start_pos = min_coord.x + 0.5*tip_thickness - overlapping_distance
#    x_end_pos = max_coord.x - 0.5*tip_thickness + overlapping_distance
#    y_start_pos = min_coord.y + 0.5*tip_thickness - overlapping_distance

#    y_increment = tip_thickness - overlapping_distance

#    debug_mode = False
#    if debug_mode:
#        print()
#        print('### Debug Values for ink laying gcode generator Function ###')
#        print(x_min_max, y_min_max, ': board outline')
#        print(y_length, tip_thickness, ': y-length and tip thickness')
#        print(OD_min_value, OD_max_value, ': OD limits')
#        print(num_ys_max_value, num_ys_min_value, ': ys limits')
#        print(results)
#        print(num_ys, overlapping_distance)
#        print(x_start_pos, y_start_pos, ': start positions')
#        print(x_end_pos, ': end positions')
#        print(y_increment, ': y increment')
#        print('### End ###')
#        print()
#        print()


#    ### G-Code to be generated ###
#    gcode = ''

#    gcode += '\n; The following gcode is the ink laying gcode\n'
#    gcode += f'; According to input gerber file it will have {num_ys} number of y iterations and Over-lapping distance is {overlapping_distance}\n\n'

#    # Select Tool number 3, The Pen
#    gcode += tool(ToolChange.Select, Tool.Pen)

#    # Activate Tool number 3, The Pen
#    # gcode += 'M3 S250 ; Turn Pen ON\n\n' #TODO:

#    # Set the slow feedrate to be used for ink laying
#    gcode += f'F{feedrate} ; setting default feedrate for ink laying\n\n'

#    # Go to starting position
#    gcode += move(MotionMode.RAPID, comment='; Go to ink laying starting position', x=x_start_pos, y=y_start_pos, z=pen_down_position)

#    # Execute the MAIN Gcode
#    current_x_dict = {False: x_start_pos, True: x_end_pos}
#    current_x_ind = False
#    current_y = y_start_pos  # must add the y start position before adding increments
#    for _ in range(num_ys):
#        current_x_ind = not current_x_ind
#        current_x = current_x_dict[current_x_ind]
#        current_y += y_increment

#        gcode += move(x=current_x)
#        gcode += move(y=current_y)
#    gcode += '\n'

#    # Get tool away from PCB in Z position
#    gcode += move(MotionMode.RAPID, comment='Get away from PCB in Z axis\n', z=0)

#    # Deactivate End Effector Signal
#    gcode += f'M5 ; Disable End-Effector Signal\n\n'

#    # Get the tool back and deselect it
#    gcode += tool(ToolChange.Deselect, Tool.Pen)

#    return gcode


def generate_laser_engraving_trace_gcode(gerber_obj: gerber.rs274x.GerberFile, settings) -> str:
    '''
    :param gerber_file: the file that we want to get the holes coordinate from

    :param settings: number of passes done by laser

    :return: This function creates the gcode content as string according to the input coordinates
    '''
    gcode = ''

    gcode += '\n; PCB trace laser engraving Gcode\n\n'

    # Setting GRBL mode to laser mode
    gcode += "; Please Check $32 is equal to 1 for Laser Mode\n\n"

    # Activiate Tool number 1, The Laser Module
    if settings.tool:
        gcode += settings.tool(ToolChange.Select, settings.Tool.Laser)
    
    # Setting the laser module movment feedrate
    gcode += f'F{settings.feedrate} ; setting default feedrate\n\n'

    # Setting the Optimum focal distance by moving the Z position in the correct coordinate
    gcode += move(MotionMode.RAPID, comment='Moving to correct focal length Z position\n', z=settings.optimum_focal_distance)

    # Setting the correct laser Power
    gcode += f"S{settings.laser_power} ; Setting Laser Power\n\n"

    ### PCB trace laser marking Gcode
    # Getting Offset Points for laser module to burn in 
    # The bulk of the code is in this single line ;)
    coordinate_lists = get_traces_outlines(gerber_obj, settings.include_edge_cuts, debug=settings.debug)  

    gcode += f"; Number of passes: {settings.laser_passes}\n\n"
    for pass_num in range(laser_passes):
        gcode += f'; Pass number: {settings.pass_num+1}\n'

        for coordinate_list in coordinate_lists:
            gcode += move(coordinate=coordinate_list[0])
            gcode += "M3\n"

            for coordinate in coordinate_list[1:]:
                gcode += move(coordinate=coordinate)

            gcode += move(coordinate=coordinate_list[0])  #TODO: ??!??!?! what is this ???!?!
            gcode += "M5\n"

    gcode += '\n'

    # Deactivate End Effector Signal
    gcode += f'M5 ; Disable End-Effector Signal\n\n'

    # Get the tool back and deselect it
    if settings.tool:
        gcode += tool(ToolChange.Deselect, settings.Tool.Laser)

    return gcode

def generate_spindle_engraving_trace_gcode(gerber_obj: gerber.rs274x.GerberFile, settings) -> str:
    '''
    :param gerber_file: the file that we want to get the holes coordinate from
    :param settings: the settings parameter

    :return: This function creates the gcode content as string according to the input coordinates
    '''
    ### Preparations
    # getting the list of list of path coords :D
    # The bulk of the code is in this single line ;)
    # Preparing Height Map
    if settings.height_map:
        with open(settings.height_map, 'r') as f:
            height_map = json.load(f)
    else:
        height_map = None
    coordinate_lists = get_traces_outlines(
            gerber_obj, 
            settings.include_edge_cuts, 
            settings.spindle_bit_offset, 
            height_map=height_map, 
            Z_offset_from_0=settings.spindle_Z_down_engrave,
            debug=settings.debug)

    ### Gcode
    gcode = ''

    gcode += '\n; Spindle trace Spindle engraving Gcode\n\n'

    # Setting GRBL mode to spindle mode
    gcode += "; Please Check $32 is equal to 0 for Spindle Mode\n\n"

    #  Starting Spindle and Setting the correct spindle speed
    gcode += set_non_modal_options(spindle_speed=settings.spindle_speed,
            feedrate=settings.spindle_feedrate_XY_engrave,
            comment="Settings Non Modal Groups")

    # Making sure Modal Group settings are correct
    gcode += set_modal_options(MotionMode.USE_FEEDRATE, 
            DistanceMode.ABSOLUTE, 
            UnitMode.MM, 
            PlaneSelect.XY, 
            FeedRateMode.UNIT_PER_MIN,
            comment="Setting Modal Groups\n")

    # Starting Spindle Away from surface
    gcode += move(MotionMode.RAPID,
            DistanceMode.ABSOLUTE,
            Z=2,
            comment="Going Up from surface to start spindle")
    gcode += set_modal_options(SpindleState.ON_CW, 
            comment="Spindle ON CW")
    gcode += dwell(2, comment="dwell for 2 seconds so motor reaches full RPM\n")
    
    ### PCB trace engraving Gcode
    for ind, coordinate_list in enumerate(coordinate_lists):
        gcode += f"; Engraving Trace No. {ind}\n"

        # Go to start of Loop
        gcode += move(MotionMode.RAPID, 
                    coordinate=Point(coordinate_list[0].x,
                                    coordinate_list[0].y,
                                    settings.spindle_Z_up_position),
                    feedrate=settings.spindle_feedrate_XY_engrave)

        # Spindle Down, Start engraving
        gcode += move(Z=coordinate_list[0].z, feedrate=settings.spindle_feedrate_Z_engrave)

        # Setting engraving feedrate
        gcode += set_non_modal_options(feedrate=settings.spindle_feedrate_XY_engrave,
                                        comment="setting default feedrate")

        # Continue Loop
        for coordinate in coordinate_list[1:]:
            gcode += move(coordinate=coordinate)

        # Complete the Loop
        gcode += move(coordinate=coordinate_list[0])

        # CCW spindle movement if wanted
        if settings.add_spindle_trace_ccw_path:
            gcode += f"\n; Engraving Trace No. {ind} CCW\n"
            for coordinate in coordinate_list[::-1]:
                gcode += move(coordinate=coordinate)

        # Spindle Up, Stop engraving
        gcode += move(Z=settings.spindle_Z_up_position, feedrate=settings.spindle_feedrate_Z_up)

        gcode += '\n'

    # Deactivate End Effector Signal
    gcode += set_modal_options(SpindleState.OFF, comment="Disable Spindle\n")

    return gcode

def export_gcode(gcode: str, file_name: str) -> None:

    '''
    :param gcode: the actual gcode file content
    :param file_name: the wanted gcode filename
    creates the gcode file
    '''
    with open(file_name, 'w') as g_file:
        g_file.write(gcode)

@contextmanager
def temp_timeout(ser, timeout: int):
    '''
    applies a timeout to some serial code then return to default timeout automagically :)
    '''
    old_timeout = ser.timeout
    ser.timeout = timeout
    try:
        yeild
    finally:
        ser.timeout = old_timeout

@dataclass
class Offset:
    x: float
    y: float
    z: float

class GenerateHeightMap:
    '''
    Object to handle all the sending and receiving to grbl to get the height map!
    '''
    def __init__(self, gerber_obj: gerber.rs274x.GerberFile, settings):
        '''
        Main Routine to generate the height map
        '''
        ### Creating some essential attributes
        self.gerber_obj = gerber_obj
        self.settings = settings
        self.height_map = self.generate_height_map_datastructure()
        
        ### Starting the Sequence
        self.check_user_is_ready()

        # Establishing Connection
        with serial.Serial(self.settings.serial_port, self.settings.serial_baud, timeout=2) as ser:
            self.read_grbl_initial_msg(ser)
            self.g54_offset, self.g92_offset = self.get_grbl_g54_g92_offsets(ser)
            #TODO: Make sure we are on the G54 offset

            for ind, coord in enumerate(self.height_map):
                # Step 1: Go next height map grid point
                ser.write(move(MotionMode.RAPID, 
                    DistanceMode.ABSOLUTE, 
                    z=1).encode())
                ser.write(move(MotionMode.RAPID, 
                    DistanceMode.ABSOLUTE, 
                    x=coord[0], y=coord[1]).encode())

                # Step2: Confirm Command is received
                confirmation = ser.readline().decode()
                confirmation += ser.readline().decode()
                if 'ok' not in confirmation:
                    raise ValueError("Didn't receive 'ok' after sending gcode")
                else:
                    print(f"Getting Probe Value at Coord({coord[0]}, {coord[1]}) -> ({ind}/{len(self.height_map)-1})")

                # Step3: Send Probe Command
                ser.write(move(MotionMode.PROBE_TOWARD_ERROR, 
                               DistanceMode.INCREMENTAL,
                               z=-2,
                               feedrate=10).encode())

                # Step4: Process Probe response
                probe_value_response = ser.readline().decode()
                while 'PRB' not in probe_value_response:
                    probe_value_response = ser.readline().decode()
                    if 'alarm' in probe_value_response.lower():
                        raise ValueError(f"ALARM detected!!\n{probe_value_response}")
                matches = re.findall(r"\[PRB:([^,]+),([^,]+),([^,:]+)", probe_value_response)
                if matches:
                    probe_value = round(float(matches[0][2]) - self.g54_offset.z - self.g92_offset.z, 4)
                    print(f"Got Probe Value: {probe_value}\n")
                else:
                    raise ValueError(f"Couldn't regex match the probe string!!\nProbe String from Grbl: {probe_value_response}")
                
                # Step 5: Save height map value :D
                # finally, skeywordet the probe Z value
                self.height_map[ind][2] = probe_value 
        
            # Go back to ORIGIN
            ser.write(move(MotionMode.RAPID,
                           DistanceMode.ABSOLUTE,
                           x = 0, y = 0, z = 2).encode())

    def check_user_is_ready(self):
        '''
        Checks if user has the ASSUMPTIONS CORRECT
        '''
        user_in = input("\nASSUMING THE GRBL CURRENT WORKING COORDINATE X, Y, Z ORIGIN IS AT ORIGIN OF PCB( (0, 0, 0) of PCB ).\nASSUMING Z=0 IS JUST TOUCHING PCB surface.\nASSUMING PROBE IS ATTACHED TO BIT!\n\nConfirm (y/n): ").lower()
        if user_in == 'n':
            raise ValueError("Aborting Execution due to User input..")
        elif user_in not in ['y', 'yes']:
            raise ValueError("Unknown answer.")
        print()

    def generate_height_map_datastructure(self) -> list[list[float, float, float]]:
        '''
        generate the datastructure of the height map
        '''
        height_map = []
        x_size = self.gerber_obj.size[0]  # max pcb length in mm
        y_size = self.gerber_obj.size[1]  # max pcb width in mm
        for x in range(0, ceil(x_size), self.settings.height_map_resolution):
            for y in range(0, ceil(y_size), self.settings.height_map_resolution):
                height_map.append([x, y, 0])
        height_map.append([ceil(x_size), ceil(y_size), 0])  # Making sure not out of bound coords can be passed to interpolation function
        return height_map

    def read_grbl_initial_msg(self, ser: serial.Serial):
        '''
        read the "GrblHAL 1.1f ['$' or '$help' for help]"
        '''
        # reading the greeting grbl message first
        response = ser.readline().decode()
        response += ser.readline().decode()
        if 'grbl' not in response.lower():
            raise ValueError("Expected Grbl Greeting Message Upon connection!")
        else:
            print("\nEstablished Successful Connection to GRBL Device!\n")

    def get_grbl_g54_g92_offsets(self, ser: serial.Serial) -> tuple[Offset, Offset]:
        '''
         - Check grbl device responsive
         - use '$#' to check the G54 and G92 offsets

         current absolute coord = machine coord - G54 coord - G92 coord
         (use '?' to check absolute machine coord)
        '''
        # set timeout to 2 seconds as $# shouldn't take any time to respond
        ser.timeout = 2

        # send the $# command to get all the GRBL offsets
        ser.write('$#\n'.encode())

        # keep reading until nothing else to read
        tmp = ser.readline().decode()
        response = ""
        response += tmp
        while tmp != '':
            tmp = ser.readline().decode()
            response += tmp

        # extracting the G54 and G92 offsets into the Offset datastructure
        g54_match = re.search(r"\[G54:([-\d.]+),([-\d.]+),([-\d.]+)\]", response)
        if g54_match:
            g54_offset = Offset(
                    float(g54_match.group(1)),
                    float(g54_match.group(2)),
                    float(g54_match.group(3))
                    )
        else:
            raise ValueError(f"Couldn't extract G54 offsets?!\nResponse: {response}")

        g92_match = re.search(r"\[G92:([-\d.]+),([-\d.]+),([-\d.]+)\]", response)
        if g92_match:
            g92_offset = Offset(
                    float(g92_match.group(1)),
                    float(g92_match.group(2)),
                    float(g92_match.group(3))
                    )
        else:
            raise ValueError(f"Couldn't extract G92 offsets?!\nResponse: {response}")

        print(f"G54 Offset: {g54_offset}\nG92 Offset: {g92_offset}\n")
        return g54_offset, g92_offset


if __name__ == '__main__':

    #NOTE!!!! The gerber file is assumed to be mirrorred!!!!!

    gerber_file_path = 'gerber_files/test2.gbr'
    # gerber_file_path = 'gerber_files/test.gbr'

    gcode_file_path = 'gcode_files/default.gcode'

    # new_file_name = 'test2.gbr'

    ##### Tweaking Arguments #####

    # Offset PCB from (0, 0)
    x_offset = 2
    y_offset = 2

    ### Tool Home positions and latch offset (as absolute values)
    X_latch_offset_distance_in = 188  # ABSOLUTE value
    X_latch_offset_distance_out = 92  # ABSOLUTE value
    attach_detach_time = 5 # the P attribute in Gcode is in seconds
    tool_home_coordinates = {1: Point(165, 0, 11), 2: Point(165, 91, 12), 3: Point(165, 185.5, 12)}  # ABSOLUTE values

    tool_offsets = {0: Point(0, 0, 0), 1: Point(0, 0, 0), 2: Point(0, 0, 0), 3: Point(0, 0, 0)}  #TODO: find this value ASAP, 

    tool = get_tool_func(X_latch_offset_distance_in, X_latch_offset_distance_out, tool_home_coordinates, tool_offsets, attach_detach_time)

    ### spindle tweaking values
    # Z positions
    router_Z_up_position = 20
    router_Z_down_position = 25
    # Feedrates
    router_feedrate_XY = 700
    router_feedrate_Z = 10
    # Power intensities
    spindle_speed = 230

    ### Pen Tweaking Valuesgenerate_pcb_trace_gcode
    # Z positions
    pen_down_position = 10 
    # Feedrates
    ink_laying_feedrate = 100
    # Tip Thickness in mm
    tip_thickness = 4

    ### Laser Module Tweaking Values
    # Z positions
    optimum_laser_Z_position = 16  # 44mm from laser head to PCB
    # Feedrates
    pcb_trace_feedrate = 600
    # Power intensities
    laser_power = 150 


    ### Main Code ###
    # Read the gerber file
    gerber_obj = gerber.read(gerber_file_path)

    # Mirror Gerber File
    gerber_obj.mirror()

    # Recenter Gerber File with wanted Offset
    gerber_obj.recenter_gerber_file(x_offset, y_offset)

    # writing new gbr after mirroring and recentering
    gerber_obj.write(gcode_file_path)

    # gcode = ''

#     # Creating the holes_gcode
#     gcode += generate_holes_gcode(gerber_obj, tool, router_Z_up_position, router_Z_down_position, router_feedrate_XY, router_feedrate_Z, spindle_speed, terminate_after = False)

#     # Creating the PCB ink laying Gcode
#     gcode += generate_ink_laying_gcode(gerber_obj, tool, tip_thickness, pen_down_position, ink_laying_feedrate, initiated_before=True, terminate_after = False)

    # # Creating the PCB trace laser Toner Transfer Gcode
    # gcode += generate_laser_engraving_trace_gcode(gerber_obj, tool, optimum_laser_Z_position, pcb_trace_feedrate, laser_power, debug=True)

    # # exporting the created Gcode
    # export_gcode(gcode, new_file_name)


