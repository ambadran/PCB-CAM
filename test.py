import gerber
from cam import GerberToShapely, visualize, visualize_group

gbr_obj = gerber.read("gerber_files/arc_obj.gbr")



test = GerberToShapely(gbr_obj.primitives[-2])



visualize(test, x_offset = 150, y_offset = -110, multiplier = 40, terminate = True)
