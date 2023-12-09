'''
Python script to implement terminal command functionality

To test the laser gcode for example

python3 cli.py -D test.gcode --laser --debug-laser gerber_files/mirrored_and_offseted.gbr
'''
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from main import Settings, main
from default_settings import default_settings_dict
from typing import Optional

def addArg(name: str, help_str: str, var_type, one_letter: Optional[str]=None) -> None:
    '''
    implements parser.add_argument() easily
    '''
    global parser
    global default_settings_dict

    if '-' in name:
        raise ValueError('Please enter the python name (with _ not -)')

    if '_' in name:
        cli_name = name.replace('_', '-')
    else:
        cli_name = name

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
    addArg('dest', "Destination Gcode file", str, 'D')

    addArg('mirrored', "Mirror Given Srouce Gerber file. Used for traces of DIP components", bool, 'M')

    addArg('x_offset', "Value PCB offseted from X axis", int)
    addArg('y_offset', "Value PCB offseted from Y axis", int)

    addArg('all_gcode', "Creates a Gcode file with hole drilling gcode, ink laying gcode and laser drawing gcode", bool, 'ALL')
    addArg('holes', "Adds hole drilling gcode to Gcode file", bool)
    addArg('ink', "Adds ink laying gcode to Gcode file", bool)
    addArg('laser', "Adds laser drawing gcode to Gcode file", bool)
    addArg('include_edge_cuts', "Include Edge cuts in laser marking process", bool)
    addArg('laser_passes', "Number of passes for laser marking Gcode", int)
    addArg('debug_laser', "Shows Simulation of the PCB laser trace coordinates", bool)

    ### Extracting User inputs!
    # Getting arguments
    settings.settings_dict.update(vars(parser.parse_args()))

    ### Executing the Program!
    main(settings)

