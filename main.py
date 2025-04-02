'''
PCB CAM program 

My custom Gcode Generator :)))
'''
import warnings
with warnings.catch_warnings():
    # suppressing a stupid syntax warning to convert 'is not' to '!='
    warnings.filterwarnings("ignore", category=SyntaxWarning)
    import gerber

from gcode_tools import *
import default_settings
import os

class Settings:
    '''
    Class to make it easier to call and manipulate settings
    '''
    default_settings_dict = default_settings.default_settings_dict

    def __init__(self, input_settings_dict = {}):
        self.settings_dict = {}

        if input_settings_dict:
            self.settings_dict.update(input_settings_dict)

    def __getattr__(self, key):
        if key not in self.settings_dict:
            return self.default_settings_dict[key]

        else:
            return self.settings_dict[key]

    @property
    def tool(self):
        '''
        This function prepares end effector for multi-tool CNC machines.
        There are two types of multi-tool CNC machines

        1- Uses Kinematic mounting mechanisms that  need the end effector to attach to a specific tool (laser engraver) then latch onto it and then pull out.
        2- Uses Spindle bit change mechanisms.
        '''
        if self.kinematic_mounting_mechanism:
            return get_tool_func(self.X_latch_offset_distance_in, self.X_latch_offset_distance_out, self.tool_home_coordinates, self.tool_offsets, self.attach_detach_time)

        elif self.spindle_bit_change:
            #TODO: need to re-write ALL the tool functions to accomodate all possibilites
            pass


def main(settings: Settings):
    '''
    ### Main Code ###
    '''
    # Error checking the arguments
    if settings.create_height_map and (settings.holes or settings.laser or settings.spindle):
        raise ValueError("can't create height map and generate PCB gcode at once!")

    elif not settings.create_height_map:
        if not settings.holes and not settings.laser and not settings.spindle:
            raise ValueError("\nMust choose what Gcode to export!\nOptions:\n1- '--all-gcode' : exports all 3 gcodes\n2- '--holes' : Adds hole drilling gcode to Gcode file\n3- '--ink' : Adds ink laying gcode to Gcode file\n4- '--laser' : Adds laser drawing gcode to Gcode file")
        if settings.laser and settings.spindle:
            raise ValueError("\nCan't have two engraving methods! Please either spindle OR laser.")

    ### Processing the Gerber file
    # Read the gerber file
    gerber_obj = gerber.read(settings.src)

    # Recenter Gerber File with wanted Offset
    gerber_obj.recenter_gerber_file(settings.x_offset, settings.y_offset)

    # Mirror Gerber File
    if settings.mirrored:
        gerber_obj.mirror()

    # Rotate Gerber File
    if settings.rotated:
        gerber_obj.rotate_90()

    # height_map mode
    if settings.create_height_map:
        height_map = generate_height_map(gerber_obj, settings)
        
        dir_path = os.path.dirname(settings.src)
        dir_path_with_slash = dir_path if dir_path.endswith('/') else dir_path + '/'
        with open(dir_path_with_slash+settings.created_height_map_default_file_name, "w") as f:
            json.dump(height_map, f)

        return None

    # Saving New Gerber File
    if not settings.dont_export_gbr:
        dir_path = os.path.dirname(settings.src)
        dir_path_with_slash = dir_path if dir_path.endswith('/') else dir_path + '/'
        gerber_obj.write(dir_path_with_slash + settings.new_gbr_name)

    ### Creating the Gcode file
    gcode = ""
    debug_msg = f"\n\nPCB Dimension Width: {gerber_obj.size[0]}, Height: {gerber_obj.size[1]}.\n\n"

    gcode += general_machine_init()
    gcode += f"\n; PCB Dimension Width: {gerber_obj.size[0]}, Height: {gerber_obj.size[1]}.\n"

    ### DEPRECATED ###
    # # Creating the PCB ink laying Gcode
    # if settings.all_gcode or settings.ink:
    #     gcode += generate_ink_laying_gcode(gerber_obj, settings.tool, settings.tip_thickness, 
    #                                        settings.pen_down_position, settings.ink_laying_feedrate, debug=settings.debug)
    #     debug_msg += "Exported Ink Laying Gcode..\n"
    ##################

    # Creating the PCB traces by spindle engraving
    if settings.spindle:
        gcode += generate_spindle_engraving_trace_gcode(gerber_obj, settings)
        debug_msg += "Exported Spindle PCB engraving Gcode..\n"

    # Creating the PCB traces by laser engraving
    if  settings.laser:
        gcode += generate_laser_engraving_trace_gcode(gerber_obj, settings)
        debug_msg += "Exported laser PCB engraving Gcode..\n"

    # Creating the holes_gcode
    if settings.holes:
        gcode += generate_holes_gcode(gerber_obj, settings)
        debug_msg += "Exported spindle hole drilling Gcode..\n"

    # Machine Deinit
    gcode += general_machine_deinit()

    # exporting the created Gcode
    export_gcode(gcode, settings.dest)

    # End statement
    print(debug_msg)


# just a test
if __name__ == '__main__':

    ### default settings dict 
    default_settings_dict = {

        # Offset PCB from (0, 0)
        "offset": 2,
        "y_offset": 2,

        ### Tool Home positions and latch offset (as absolute values)
        "X_latch_offset_distance_in": 188,  # ABSOLUTE value
        "X_latch_offset_distance_out": 92,  # ABSOLUTE value
        "attach_detach_time": 5, # the P attribute in Gcode is in seconds
        "tool_home_coordinates": {1: Point(165, 0, 11), 
                                2: Point(165, 91, 12), 
                                3: Point(165, 185.5, 12)},  # ABSOLUTE values

        "tool_offsets": {0: Point(0, 0, 0), 
                       1: Point(0, 0, 0), 
                       2: Point(0, 0, 0), 
                       3: Point(0, 0, 0)},  #TODO: find this value ASAP, 


        ### spindle tweaking values
        # Z positions
        "router_Z_up_position": 20,
        "router_Z_down_position": 25,
        # Feedrates
        "router_feedrate_XY": 700,
        "router_feedrate_Z": 10,
        # Power intensities
        "spindle_speed": 230,

        ### Pen Tweaking Values
        # Z positions
        "pen_down_position": 10,
        # Feedrates
        "ink_laying_feedrate": 100,
        # Tip Thickness in mm
        "tip_thickness": 4,

        ### Laser Module Tweaking Values
        # Z positions
        "optimum_laser_Z_position": 16,  # 44mm from laser head to PCB
        # Feedrates
        "pcb_trace_feedrate": 600,
        # Power intensities
        "laser_power": 150,

        # mirrored
        'mirrored': True,

        # Gcode Modes
        'all_gcode': False,
        'ink': False,
        'laser': True,
        'holes': True,

        # Show Gcode Creation Debugging info and visualization :)
        'debug': True,

        # other options

        'dont_export_gbr': False,  # saves the gbr file after recenter and mirror (if settings allow it)
        'new_gbr_name': 'mirrored_and_offseted.gbr'
    }

    ### Settings
    settings = Settings(default_settings_dict)

    ### Source File
    settings.src = 'gerber_files/default.gbr'

    ### Destination File
    settings.dest = 'gcode_files/test.gcode'

    ### Executing the Program!
    main(settings)

