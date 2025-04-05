from shapely import Point

default_settings_dict = {

    # Offset PCB from (0, 0)
    "x_offset": 2,
    "y_offset": 2,

    ### Tool change settings
    'spindle_bit_change': False,
    'kinematic_mounting_mechanism': False,

    ### Spindle Bit Change Settings
    #TODO:

    ### Kinematic Mounting Mechanism settings
    # Tool Home positions and latch offset (as absolute values)
    "X_latch_offset_distance_in": 188,  # ABSOLUTE value
    "X_latch_offset_distance_out": 92,  # ABSOLUTE value
    "attach_detach_time": 5, # the P attribute in Gcode is in seconds
    "tool_home_coordinates": {1: Point(165, 0, 10.5), 
                            2: Point(165, 91, 12), 
                            3: Point(165, 185.5, 12)},  # ABSOLUTE values

    "tool_offsets": {0: Point(0, 0, 0), 
                   1: Point(0, 0, 0), 
                   2: Point(0, 0, 0), 
                   3: Point(0, 0, 0)},  #TODO: find this value ASAP, 


    ### spindle tweaking values
    # Z positions
    "spindle_Z_up_position": 1,
    "spindle_Z_down_engrave": 0.02,
    "spindle_Z_down_hole": 2,
    # Feedrates
    "spindle_feedrate_XY_engrave": 200,
    "spindle_feedrate_XY_hole": 600,
    "spindle_feedrate_Z_engrave": 30,
    "spindle_feedrate_Z_hole": 50,
    "spindle_feedrate_Z_up": 100,
    # Power intensities
    "spindle_speed": 400,
    # Spindle Bit Offset for engraving
    "spindle_bit_offset": 0.2,

    # ### Pen Tweaking Values
    # # Z positions
    # "pen_down_position": 10,
    # # Feedrates
    # "ink_laying_feedrate": 100,
    # # Tip Thickness in mm
    # "tip_thickness": 4,

    ### Laser Module Tweaking Values
    # Z positions
    "optimum_laser_Z_position": 16,  # 44mm from laser head to PCB
    # Feedrates
    "pcb_trace_feedrate": 400,
    # Power intensities
    "laser_power": 200,
    # Include edge cut in pcb laser marking
    "include_edge_cuts": False,
    # Laser Gcode Passes
    "laser_passes": 1,

    # destination
    'dest': './default.gcode',

    # mirrored
    'mirrored': False,

    # rotated
    'rotated': False,

    # Gcode Modes
    # 'ink': False, # deprecated
    'laser': False,
    'spindle': False,
    'holes': False,

    # Show Gcode Creation Debugging info and visualization :)
    'debug': False,

    # other options

    'dont_export_gbr': False,  # saves the gbr file after recenter and mirror (if settings allow it)
    'new_gbr_name': 'mirrored_and_offseted.gbr',

    'create_height_map': False, # executed when triggered
    'serial_port': "/dev/ttyACM0",
    'serial_baud': 115200,
    'height_map_resolution': 5,
    'created_height_map_default_file_name': "height_map.json",
    'height_map': "height_map.json", # default height map to use

}


