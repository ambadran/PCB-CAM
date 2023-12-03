'''
This script uses python gerber library to read and parse any gerber file.
Then uses shapely to create outline gcode and holes gcode.
'''
from __future__ import annotations
import gerber
from shapely import Point, MultiPoint



if __name__ == '__main__':
    gerber_file = 'gerber_files/default.gbr'
    
    gerber_obj = gerber.read(gerber_file)
