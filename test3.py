from shapely import Polygon, LineString, LinearRing
import turtle
import random
from matplotlib import patches, path
import numpy as np

def visualize(line_string: LineString, hide_turtle=True, speed=0, x_offset=40, y_offset=20, line_width=1.5, multiplier=8, terminate=False) -> None:
    '''
    visualizes the linked list
    '''
    if type(line_string) != LineString and type(line_string) != LinearRing and type(line_string) != Polygon:
        raise ValueError("Must be of type shapely LineString")

    turtle_window_size_x = 850
    turtle_window_size_y = 580
    turtle.Screen().setup(turtle_window_size_x, turtle_window_size_y)
    skk = turtle.Turtle()
    turtle.width(line_width)
    turtle.speed(speed)
    if hide_turtle:
        turtle.hideturtle()
    else:
        turtle.showturtle()

    colors = ['black', 'red', 'blue', 'light blue', 'green', 'brown', 'dark green', 'orange', 'gray', 'indigo']
    color = random.choice(colors)
    # while color in Graph.used_colors:
    #     color = random.choice(colors)

    turtle.pencolor(color)
    if type(line_string) == Polygon:
        coord_list = list(line_string.exterior.coords)

    else:
        coord_list = list(line_string.coords)

    turtle.up()
    turtle.setpos((coord_list[0][0] - x_offset) * multiplier, (coord_list[0][1] - y_offset) * multiplier)
    turtle.down()
    for coord in coord_list[1:-1]:
        turtle.setpos((coord[0] - x_offset) * multiplier, (coord[1] - y_offset) * multiplier)

    turtle.setpos((coord_list[-1][0] - x_offset) * multiplier, (coord_list[-1][1] - y_offset) * multiplier)
    # if coord_list[0] == coord_list[-1]:
    #     turtle.setpos((coord_list[0][0] - x_offset) * multiplier, (coord[1] - y_offset) * multiplier)

    # Graph.used_colors.add(color)
    # if len(Graph.used_colors) == len(colors):
    #     print('\n\n!!!!!!!!!! COLORS RESET !!!!!!!!!!!!!!!!!\n\n')
    #     Graph.used_colors = set()

    if terminate:
        turtle.done()


class RoundedPolygon(patches.PathPatch):
    def __init__(self, xy, pad, **kwargs):
        p = path.Path(*self.__round(xy=xy, pad=pad))
        super().__init__(path=p, **kwargs)

    def __round(self, xy, pad):
        n = len(xy)

        for i in range(0, n):

            x0, x1, x2 = np.atleast_1d(xy[i - 1], xy[i], xy[(i + 1) % n])

            d01, d12 = x1 - x0, x2 - x1
            d01, d12 = d01 / np.linalg.norm(d01), d12 / np.linalg.norm(d12)

            x00 = x0 + pad * d01
            x01 = x1 - pad * d01
            x10 = x1 + pad * d12
            x11 = x2 - pad * d12

            if i == 0:
                verts = [x00, x01, x1, x10]
            else:
                verts += [x01, x1, x10]
        codes = [path.Path.MOVETO] + n*[path.Path.LINETO, path.Path.CURVE3, path.Path.CURVE3]

        return np.atleast_1d(verts, codes)


polygon = Polygon(LinearRing([(0, 0), (10, 0), (10, 10), (0, 10)]))
coords = list(polygon.exterior.coords)

xy = np.array(coords[:-1])
rounded_polygon = RoundedPolygon(xy=xy, pad=0.1)

weird_coords = list(rounded_polygon.get_path().vertices)
coords_list = []
for val in weird_coords:
        coords_list.append((val[0], val[1]))

line_string = LineString(coords_list)
visualize(line_string, terminate=True)
