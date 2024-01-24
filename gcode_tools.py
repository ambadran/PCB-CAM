'''
This file has function to generate the gcode we want
'''
from enum import Enum
from typing import Callable, Optional
from math import floor, ceil
from cam import get_laser_coords, get_holes_coords, get_pen_coords, Point, gerber

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


class ToolChange(Enum):
    Deselect = 0
    Select = 1


class CoordMode(Enum):
    ABSOLUTE = 0
    INCREMENTAL = 1


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
                    raise ValueError(f"Point list must only contain integers or floats, passed type is {type(value[0]), type(value[1])}")

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
                except Exception:
                    raise ValueError(f"Point list must only contain integers or floats, passed type is {type(value[0]), type(value[1])}")

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


def set_grbl_coordinate(coordinate_mode: CoordMode, comment: Optional[str]=None, **coordinate) -> str:
    '''
    overwrites the current grbl working coordinate
    :param kwargs: must input either coordinate=[x, y] or one of x=int, y=int, z=int or a combination of those three

    :return: gcode line of the wanted inputs
    '''
    comment_available = False

    if coordinate_mode == CoordMode.ABSOLUTE:
        gcode = "G10 P0 L20 "
    elif coordinate_mode == CoordMode.INCREMENTAL:
        gcode = '#TODO '
    else:
        raise ValueError("Unsupported Mode!")

    gcode += get_coordinate_from_kwargs(coordinate)

    if comment:
        gcode += f" ; {comment}"

    gcode += '\n'

    return gcode


def general_machine_init() -> str:
    '''
    Normal initiation routines to make sure the machine will work fine

    :returns: machine initiation gcode
    '''
    gcode = ''

    # G-Code to be generated
    gcode += '; This gcode is generated by my specialised python script for my PCB manufacturer project :))\n\n'

    gcode += '; Machine Initialization Sequence...\n\n'

    gcode += 'G21 ; to set metric units\n'
    gcode += 'G90 ; to set absolute mode , G91 for incremental mode\n'
    gcode += 'G94 ; To set the active feed rate mode to units per minute mode\n\n'


    # M5 disables spindle PWM, C0 chooses empty tool slot in multiplexer, to ensure no endeffector works by mistake 
    gcode += f'M5 ; disabling spindle PWM\n'
    gcode += f'C0 ; Choosing the empty tool slot in the multiplexer circuits\n\n'

    # Turn ON Machine
    gcode += f"B1 ; Turn ON Machine\n\n"

    # HOMING, machine is at (0, 0, 0) now
    gcode += f"$H ; Homing :)\n"

    # Make sure grbl understands it's at zero now
    gcode += set_grbl_coordinate(CoordMode.ABSOLUTE,
            comment="Force Reset current coordinates after homing\n", 
            coordinate=Point(0, 0, 0))
    
    return gcode


def general_machine_deinit() -> str:
    '''
    Normal Deinitiation routine

    :return: machine deninitiation gcode
    '''
    gcode = ''
    gcode += '; Machine deinitialization Sequence... \n'
    gcode += move(CoordMode.ABSOLUTE, use_00=True, coordinate=Point(0, 0, 0))
    gcode += 'B0 ; Turn Machine OFF\n'

    return gcode


def move(coordinate_mode: CoordMode, feedrate: Optional[int]=None, use_00: bool=False, comment: Optional[str]=None, **coordinates) -> str:
    '''
    generates movement Gxx gcode commands according to inputs

    :coordinate_mode: based on CoordMode Enum which specifies whether coordinate argument are INCREMENTAL or ABSOLUTE values
    :param feedrate: will be inserted to line if wanted
    :param use_00: use G00 to move as fast as possible without looking at current feedrate
    :param comment: add comment after gcode line
    :param **coordinates: must input either coordinate=[x, y] or one of x=int, y=int, z=int or a combination of those three
    :return: return Gxx movement gcode command as string
    '''

    if coordinate_mode == CoordMode.ABSOLUTE:
        if use_00:
            gcode = 'G00'
        else:
            gcode = 'G01 '
    elif coordinate_mode == CoordMode.INCREMENTAL:
        if use_00:
            gcode = 'G21G91G00'
        else:
            gcode = 'G21G91G01'

    gcode += get_coordinate_from_kwargs(coordinates)

    if feedrate:
        gcode += f"F{feedrate}"
    if comment:
        gcode += f" ; {comment}"

    gcode += '\n'
    
    if coordinate_mode == CoordMode.INCREMENTAL:
        gcode += 'G21G90\n'

    return gcode


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
            gcode += move(CoordMode.ABSOLUTE, use_00=True, comment=f'Go to Tool-{wanted_tool.value} Home Pos', coordinate=tool_home_coordinate)
            # Now male latch inside female latch, using incremental gcode
            gcode += move(CoordMode.ABSOLUTE,  use_00=True, comment='Enter Female Kinematic Mount Home Pos', x=latch_offset_distance_in)
            # now male latch twisting and locking on
            gcode += f"A1 ; Latch on Kinematic Mount\n"  
            # Wait until male latch is fully locked on
            gcode += f"G4 P{attach_detach_time} ; Wait for Kinematic Mount to fully attach\n"  
            # now pull off the female kinematch mount off its hanger, using incremental gcode
            gcode += move(CoordMode.ABSOLUTE,  use_00=True, comment='Exit Female Kinematic Mount Home Pos', x=latch_offset_distance_out)

            ### Fixing Current Point according the new tool head
            gcode += set_grbl_coordinate(CoordMode.INCREMENTAL, comment=' ;Add tool offset coordinate', coordinate=tool_offset)

            ### Activate it by sending the corresponding tool number in the multiplexer
            gcode += f'C{wanted_tool.value} ; Choosing tool {wanted_tool.value} in the choose demultiplexer circuits\n'

        elif tool_change_mode == ToolChange.Deselect:

            gcode += f"; Returning the Deactivating Tool-{wanted_tool.value}\n"

            ### Selecting empty tool slot in the multiplexer to stop any potential end effector action.
            gcode += 'C0 ; PWM Tool select demultiplexer to select tool zero which is the empty tool slot in multiplexers\n'

            ### Overide current coordinate to go to tool home pos relative to origin by inversing the tool_offset
            tool_offset = Point(tool_offset.x*-1, tool_offset.y*-1, tool_offset.z*-1)
            gcode += set_grbl_coordinate(CoordMode.INCREMENTAL, comment=' ;Remove tool offset coordinate', coordinate=tool_offset)

            ### Deactivate it by selecting the empty tool in the multiplexer
            # go to tool coordinate but male latch is just outside the female latch
            gcode += move(CoordMode.ABSOLUTE, use_00=True, comment=f'Go to Tool-{wanted_tool.value} Home Pos', coordinate=tool_home_coordinate)
            # Put the tool back to it's hanger
            gcode += move(CoordMode.ABSOLUTE, use_00=True, comment='Enter Female Kinematic Mount Home Pos', x=latch_offset_distance_out)
            # male latch untwisting from female latch and locking off
            gcode += f"A0 ; Latch OFF Kinematic Mount\n" 
            # Wait until male latch is fully locked off
            gcode += f"G4 P{attach_detach_time} ; Wait for Kinematic Mount to fully detach\n"
            # Now pull off the male kinematic mount away from the female kinematic mount
            gcode += move(CoordMode.ABSOLUTE, use_00=True, comment='Exit Female Kinematic Mount Home Pos', x=latch_offset_distance_in)

        else:
            raise ValueError("Mode unknown")

        gcode += '\n'
        return gcode

    return tool


def generate_holes_gcode(gerber_obj: gerber.rs274x.GerberFile, tool: Callable, motor_up_z_position: int, 
        motor_down_z_position: int, feedrate_XY: int, feedrate_Z_drilling: int, feedrate_Z_up_from_pcb: int, 
        spindle_speed: int) -> str:
    '''
    Takes in String gerber file content, identifies the PCB holes and generates the Gcode to drill the holes from begging to end!

    :param gerber: Gerber object from the gerber library
    :param tool: The tool function defined inside the get_tool_func closure function, it generates gcode to select wanted tool
    :param motor_up_z_position: position the drill bit is not touching the PCB is off a reasonable offset above the PCB
    :param motor_down_z_position: position the drill bit has completely drilled through the PCB 
    :param feedrate_XY: integer mm/minute, only for x and y movement
    :param feedrate_Z: integer mm/minute, only for z movement, which must be much slower for spindle to cut properly
    :param spindle_speed: rpm of DC motor to drill holes, please note that the value is 0-250, default value is 230 as tested.

    :return: This function creates the gcode content as string according to the input coordinates
    '''
    gcode = ''

    gcode += '\n; The following gcode is the PCB holes drill gcode\n\n'

    # Activiate Tool number 2, The Spindle
    gcode += tool(ToolChange.Select, Tool.Spindle)

    # Setting XY movement feedrate
    gcode += f'F{feedrate_XY} ; setting default feedrate\n\n'

    # setting the S value which sets pwm speed when we enable it, 
    if spindle_speed < 0 or spindle_speed > 250:
        raise ValueError("spindle_speed is only from 0-250")
    gcode += f'S{spindle_speed} ; sets pwm speed when we enable it\n\n'

    # Moving Motor to proper up Z position and home position
    gcode += move(CoordMode.ABSOLUTE, comment="Moving Spindle to UP Postion", z=motor_up_z_position, feedrate=feedrate_Z_up_from_pcb)
    gcode += '\n'

    # Turn the DC motor on and wait two seconds
    gcode += 'M3 ; Turn Motor ON\n'
    gcode += 'G4 P2 ; dwell for 2 seconds so motor reaches full RPM\n\n'

    # Cutting starts here :)

    #TODO: fix this line to return the coordinates using the python gerber library. I am still not sure how to extract componentPad coords
    coordinates = get_holes_coords(gerber_obj)

    for coordinate in coordinates:
        gcode += move(CoordMode.ABSOLUTE, coordinate=coordinate, feedrate=feedrate_XY)
        gcode += move(CoordMode.ABSOLUTE, z=motor_down_z_position, feedrate=feedrate_Z_drilling)
        gcode += move(CoordMode.ABSOLUTE, z=motor_up_z_position, feedrate=feedrate_Z_up_from_pcb)
    gcode += '\n'

    # deactivating the tool PWM
    gcode += f'M5 ; disabling spindle PWM\n\n'

    # Get the tool back to its place and deselect the tool
    gcode += tool(ToolChange.Deselect, Tool.Spindle)

    return gcode


def generate_ink_laying_gcode(gerber: gerber.rs274x.GerberFile, tool: Callable, tip_thickness: float, pen_down_position: int, 
        feedrate: int) -> str:
    '''
    :param gerber: Gerber Object from the gerber library
    :param tool: The tool function defined inside the get_tool_func closure function, it generates gcode to select wanted tool
    :param tip_thickness: number to convey thickness of pen tip in mm
    :param pen_down_position: position that pen touches PCB in Z axis
    :param feedrate: integer mm/minute, only for x and y movement for pen movement when drawing

    :return: This function creates the gcode content as string according to the input coordinates
    '''
    ### Working out the variables ###
    # Get min/max of PCB outline

    #TODO: use the new python gerber library to return edge coordinates. 
    #OLD CODE: edge_coordinates = gerber.coordinates[BlockType.Profile]
    #NEW CODE: edge_coordinates = gerber.bounds #TODO: make the output of this python gerber the same as my old output


    min_coord, max_coord = Point.get_min_max(edge_coordinates)

    # Finding num_ys and overlapping_distance
    #NOTE: Detailed description of what i am doing here is in the iPad notes
    y_length = round(max_coord.y - min_coord.y, 2)

    OD_min_value = 1
    OD_max_value = tip_thickness - 1

    num_ys_max_value = floor( ( y_length ) / (tip_thickness - OD_max_value) )
    num_ys_min_value = ceil( ( y_length ) / (tip_thickness - OD_min_value) )
    

    results = {}  # key is num_ys and value is overlapping_distance
    for num_ys in range(num_ys_min_value, num_ys_max_value+1):
        # Equation to find overlapping_distance according to given inputs, mainly the num_ys
        overlapping_distance_unrounded = (tip_thickness+num_ys*tip_thickness-y_length) / (num_ys + 2)
        overlapping_distance = round(overlapping_distance_unrounded, 2)
        results[num_ys] = overlapping_distance

    num_ys = list(results.keys())[0]  # Choosing the value with least amount of num_ys
    overlapping_distance = list(results.values())[0]  # Choosing the value with least amount of num_ys
    
    # Finding the rest of the values
    x_start_pos = min_coord.x + 0.5*tip_thickness - overlapping_distance
    x_end_pos = max_coord.x - 0.5*tip_thickness + overlapping_distance
    y_start_pos = min_coord.y + 0.5*tip_thickness - overlapping_distance

    y_increment = tip_thickness - overlapping_distance

    debug_mode = False
    if debug_mode:
        print()
        print('### Debug Values for ink laying gcode generator Function ###')
        print(x_min_max, y_min_max, ': board outline')
        print(y_length, tip_thickness, ': y-length and tip thickness')
        print(OD_min_value, OD_max_value, ': OD limits')
        print(num_ys_max_value, num_ys_min_value, ': ys limits')
        print(results)
        print(num_ys, overlapping_distance)
        print(x_start_pos, y_start_pos, ': start positions')
        print(x_end_pos, ': end positions')
        print(y_increment, ': y increment')
        print('### End ###')
        print()
        print()


    ### G-Code to be generated ###
    gcode = ''

    gcode += '\n; The following gcode is the ink laying gcode\n'
    gcode += f'; According to input gerber file it will have {num_ys} number of y iterations and Over-lapping distance is {overlapping_distance}\n\n'

    # Select Tool number 3, The Pen
    gcode += tool(ToolChange.Select, Tool.Pen)

    # Activate Tool number 3, The Pen
    # gcode += 'M3 S250 ; Turn Pen ON\n\n' #TODO:

    # Set the slow feedrate to be used for ink laying
    gcode += f'F{feedrate} ; setting default feedrate for ink laying\n\n'

    # Go to starting position
    gcode += move(CoordMode.ABSOLUTE, use_00=True, comment='; Go to ink laying starting position', x=x_start_pos, y=y_start_pos, z=pen_down_position)

    # Execute the MAIN Gcode
    current_x_dict = {False: x_start_pos, True: x_end_pos}
    current_x_ind = False
    current_y = y_start_pos  # must add the y start position before adding increments
    for _ in range(num_ys):
        current_x_ind = not current_x_ind
        current_x = current_x_dict[current_x_ind]
        current_y += y_increment

        gcode += move(CoordMode.ABSOLUTE, x=current_x)
        gcode += move(CoordMode.ABSOLUTE, y=current_y)
    gcode += '\n'

    # Get tool away from PCB in Z position
    gcode += move(CoordMode.ABSOLUTE, use_00=True, comment='Get away from PCB in Z axis\n', z=0)

    # Deactivate End Effector Signal
    gcode += f'M5 ; Disable End-Effector Signal\n\n'

    # Get the tool back and deselect it
    gcode += tool(ToolChange.Deselect, Tool.Pen)

    return gcode


def generate_pcb_trace_gcode(gerber_obj: gerber.rs274x.GerberFile, tool: Callable, optimum_focal_distance: int, 
        feedrate: int, laser_power: int, include_edge_cuts: bool, laser_passes: int, debug: bool=False) -> str:
    '''
    :param gerber_file: the file that we want to get the holes coordinate from
    :param tool: The tool function defined inside the get_tool_func closure function, it generates gcode to select wanted tool
    :param optimum_focal_distance: the distance at the laser is at its best focal distance
    :param feedrate: integer mm/minute, only for x and y movement, z movement is hardcoded here
    :param laser_power: laser intensity for toner transfer, please note that the value is 0-250, default value is 150 as tested.
    :param passes: number of passes done by laser

    :return: This function creates the gcode content as string according to the input coordinates
    '''
    gcode = ''

    gcode += '\n; The following gcode is the PCB trace laser marking gcode\n\n'

    # Activiate Tool number 1, The Laser Module
    gcode += f"M5 ; Being extra sure it won't light up before activation\n\n"
    gcode += tool(ToolChange.Select, Tool.Laser)
    
    # Setting the laser module movment feedrate
    gcode += f'F{feedrate} ; setting default feedrate\n\n'

    # Setting the Optimum focal distance by moving the Z position in the correct coordinate
    gcode += move(CoordMode.ABSOLUTE, use_00=True, comment='Moving to correct focal length Z position\n', z=optimum_focal_distance)

    # Setting the correct laser Power
    gcode += f"S{laser_power} ; Setting Laser Power\n\n"

    ### PCB trace laser marking Gcode
    # Getting Offset Points for laser module to burn in 
    # The bulk of the code is in this single line ;)
    coordinate_lists = get_laser_coords(gerber_obj, include_edge_cuts, debug=debug)  

    gcode += f"; Number of passes: {laser_passes}\n\n"
    for pass_num in range(laser_passes):
        gcode += f'; Pass number: {pass_num+1}\n'

        for coordinate_list in coordinate_lists:
            gcode += move(CoordMode.ABSOLUTE, coordinate=coordinate_list[0])
            gcode += "M3\n"

            for coordinate in coordinate_list[1:]:
                gcode += move(CoordMode.ABSOLUTE, coordinate=coordinate)

            gcode += move(CoordMode.ABSOLUTE, coordinate=coordinate_list[0])  #TODO: ??!??!?! what is this ???!?!
            gcode += "M5\n"

    gcode += '\n'

    # Deactivate End Effector Signal
    gcode += f'M5 ; Disable End-Effector Signal\n\n'

    # Get the tool back and deselect it
    gcode += tool(ToolChange.Deselect, Tool.Laser)

    return gcode


def export_gcode(gcode: str, file_name: str) -> None:

    '''
    :param gcode: the actual gcode file content
    :param file_name: the wanted gcode filename
    creates the gcode file
    '''
    with open(file_name, 'w') as g_file:
        g_file.write(gcode)


if __name__ == '__main__':

    #NOTE!!!! The gerber file is assumed to be mirrorred!!!!!

    gerber_file_path = '/home/mr-atom/Projects/PCB_manufacturer/Circuit/limit_switch/Gerber/limit_switch-F_Cu.gbr'
    # gerber_file_path = 'gerber_files/test2.gbr'
    # gerber_file_path = 'gerber_files/test.gbr'

    # gcode_file_path = 'gcode_files/default.gcode'
    gcode_file_path = '/home/mr-atom/Projects/PCB_manufacturer/Circuit/limit_switch/Gerber/mirrored_and_offseted.gbr'

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

    ### Pen Tweaking Values
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
    # gcode += generate_pcb_trace_gcode(gerber_obj, tool, optimum_laser_Z_position, pcb_trace_feedrate, laser_power, debug=True)

    # # exporting the created Gcode
    # export_gcode(gcode, new_file_name)



