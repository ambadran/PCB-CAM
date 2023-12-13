'''
#TODO: The MOST IMPORTANT TASK NOW is to implement something to prevent choosing a tool when a tool is already mounted
PCB manufacturer CAM program

My custom Gcode Generator :)))
'''
import gerber
from gcode_tools import *
import default_settings

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
        return get_tool_func(self.X_latch_offset_distance_in, self.X_latch_offset_distance_out, self.tool_home_coordinates, self.tool_offsets, self.attach_detach_time)


def main(settings: Settings):
    '''
    ### Main Code ###
    '''
    # Error checking the arguments
    if not settings.all_gcode and not settings.holes and not settings.ink and not settings.laser:
        raise ValueError("\nMust choose what Gcode to export!\nOptions:\n1- '--all-gcode' : exports all 3 gcodes\n2- '--holes' : Adds hole drilling gcode to Gcode file\n3- '--ink' : Adds ink laying gcode to Gcode file\n4- '--laser' : Adds laser drawing gcode to Gcode file")


    ### Processing the Gerber file
    # Read the gerber file
    gerber_obj = gerber.read(settings.src)

    # Recenter Gerber File with wanted Offset
    gerber_obj.recenter_gerber_file(settings.x_offset, settings.y_offset)

    # Mirror Gerber File
    if settings.mirrored:
        gerber_obj.mirror()
        pass

    ### Creating the Gcode file
    gcode = ''

    # Machine Init
    gcode += general_machine_init()

    # Creating the PCB ink laying Gcode
    if settings.all_gcode or settings.ink:
        gcode += generate_ink_laying_gcode(gerber_obj, settings.tool, settings.tip_thickness, 
                                           settings.pen_down_position, settings.ink_laying_feedrate)

    # Creating the PCB trace laser Toner Transfer Gcode
    if settings.all_gcode or settings.laser:
        gcode += generate_pcb_trace_gcode(gerber_obj, settings.tool, settings.optimum_laser_Z_position, 
                settings.pcb_trace_feedrate, settings.laser_power, settings.include_edge_cuts, settings.laser_passes, 
                debug=settings.debug_laser)

    # Creating the holes_gcode
    if settings.all_gcode or settings.holes:
        gcode += generate_holes_gcode(gerber_obj, settings.tool, settings.router_Z_up_position, 
                                      settings.router_Z_down_position, settings.router_feedrate_XY, 
                                      settings.router_feedrate_Z_drilling, settings.router_feedrate_Z_up_from_pcb,
                                      settings.spindle_speed)

    # Machine Deinit
    gcode += general_machine_deinit()

    # exporting the created Gcode
    export_gcode(gcode, settings.dest)


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
        'holes': True 

    }

    ### Settings
    settings = Settings(default_settings_dict)

    ### Source File
    settings.src = 'gerber_files/default.gbr'

    ### Destination File
    settings.dest = 'gcode_files/test.gcode'

    ### Executing the Program!
    main(settings)

