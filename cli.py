'''
Python script to implement terminal command functionality

To test the laser gcode for example

python3 cli.py -D test.gcode --laser --debug-laser gerber_files/mirrored_and_offseted.gbr
'''
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from main import Settings, main
from default_settings import default_settings_dict
from typing import Optional

def addArg(name: str, help_str: str, var_type, one_letter: Optional[str]=None, three_state: bool=False) -> None:
    '''
    implements parser.add_argument() easily

    :param three_state: if true, this will assign the 'name' variable into either of 3 values
        --name <value> -> will assign the 'name' variable into <value>
        --name          -> will assign the 'name' variable into a default value)
    and when not called -> will assign the 'name' variable into False
    '''
    global parser
    global default_settings_dict

    if '-' in name:
        raise ValueError('Please enter the python name (with _ not -)')

    if '_' in name:
        cli_name = name.replace('_', '-')
    else:
        cli_name = name

    if three_state:
        #type checking
        if var_type not in [int, float, str]:
            raise ValueError("unknown variable type for three state variables")

        if one_letter:
            parser.add_argument(
                    f"-{one_letter}",
                    f"--{cli_name}",
                    type=var_type,
                    nargs="?",
                    const=default_settings_dict[name], # default value if --name is provided
                    default=None, # default value if --name is not provided
                    help=help_str)

        else:
            parser.add_argument(
                    f"--{cli_name}", 
                    type=var_type,
                    nargs="?",
                    const=default_settings_dict[name], # default value if --name is provided
                    default=None, # default value if --name is not provided
                    help=help_str)
        return parser

    if var_type != bool:
        if one_letter:
            parser.add_argument(f'-{one_letter}', f'--{cli_name}', type=var_type, default=default_settings_dict[name], help=help_str)

        else:
            parser.add_argument(f'--{cli_name}', type=var_type, default=default_settings_dict[name], help=help_str)

    else:
        if one_letter:
            parser.add_argument(f'-{one_letter}', f'--{cli_name}', action="store_true", default=default_settings_dict[name], help=help_str)

        else:
            parser.add_argument(f'--{cli_name}', action="store_true", default=default_settings_dict[name], help=help_str)

    return parser


if __name__ == '__main__':
    # Initiating Settings object
    settings = Settings()

    ### Creating the CLI argument parser
    parser = ArgumentParser(description="Generates Custom Gcode Required by my PCB Manufacturing Machine :)", 
            formatter_class=ArgumentDefaultsHelpFormatter)

    ### Adding the positional arguments
    parser.add_argument('src', help="Source Gerber file to be converted to Gcode\n")

    ### Adding keyword Arguments
    # File management settings
    addArg('dest', "Destination Gcode file", str, 'D')
    addArg('dont_export_gbr', "Doesn't allow exporting of the mirrored_and_offseted gerber file", bool)
    addArg('new_gbr_name', "The name of the newly created Gerber File after mirroring and offsetting", str)

    # Gerber file modifications seFalsettings
    addArg('mirrored', "Mirror Gerber file. (All coordinates are mirrored)", bool, 'M')
    addArg('rotated', "Rotate Gerber file 90 degrees. (All coordinates are rotated 90d)", bool, 'R')
    addArg('x_offset', "Value PCB offseted from X axis", int)
    addArg('y_offset', "Value PCB offseted from Y axis", int)

    # Type of PCB related operations to include in Gcode
    addArg('holes', "Adds hole drilling gcode to Gcode file", bool)
    # addArg('ink', "Adds ink laying gcode to Gcode file", bool)  # deprecated
    addArg('laser', "Adds laser engraving gcode to Gcode file", bool)
    addArg('spindle', "Adds spindle engraving gcode to Gcode file", bool)

    # Tool Head change ( kinematic mounting mechanisms / spindle bit change )
    addArg('spindle_bit_change', "Adds support for CNC machines with the ability to change spindle bits.\n(Please note that the id of bit, type and size must be defined in the default_settings file or added as an argument here.)", bool)
    addArg('kinematic_mounting_mechanism', "Adds support for CNC machines with the ability to change tool head altogether using kinematic mounting mechanisms.\n(Please note that the id of the specific tool head, home position, tool offset coords MUST be defined in the default_settings file or added as an argument here.)", bool)

    # Extra settings for a specific operation
    addArg('include_edge_cuts', "Include Edge cuts in laser marking process", bool)
    addArg('laser_passes', "Number of passes for laser marking Gcode", int)
    addArg('spindle_bit_offset', "The Diameter of the spindle bit offset to make sure when engraving trace width, it is as intended", float)
    addArg('add_spindle_trace_ccw_path', "This means that the spindle will move through the trace (A->B) then (B->A). This is useful for bad bits.", bool)

    addArg('debug', "Shows Simulation of the PCB laser trace coordinates as well as other debug Info.", bool)

    # Height map command
    addArg('create_height_map', "generates height map for a PCB", bool)
    addArg('serial_port', "Serial Port Path to connect to the grbl Controller and get create height map", str)
    addArg('serial_baud', "Baud Rate of grbl Controller serial port", int)
    addArg('height_map_resolution', "When creating height map, resolution of height map in mm; take measurements every how much mm", int)
    addArg('height_map', "A path to a .json file containing height map to be taken into account in the creation of gcode", str, three_state=True)

    ### Extracting User inputs!
    # Getting arguments
    settings.settings_dict.update(vars(parser.parse_args()))

    ### Executing the Program!
    main(settings)

