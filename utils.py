
"""
Utilities used for the wrap_image and image_stamp programs

Len Wanger
last updated: 2/15/2018

"""

import math
import collections

Vertex3 = collections.namedtuple('Vertex', 'x y z')
Triangle = collections.namedtuple('Triangle', 'v1 v2 v3')

def make_triangle(d):
    """ Take a list of 3 points and return a Triangle """
    return Triangle(Vertex3(d[0][0], d[0][1], d[0][2]), Vertex3(d[1][0], d[1][1], d[1][2]), Vertex3(d[2][0], d[2][1], d[2][2]))


def cylindrical_coord(x, rads):
    x1 = x * math.cos(rads)
    y1 = x * math.sin(rads)
    return (x1, y1)


def calc_offset(c, max_c, scale, invert_offsets=False):
    fc = float(c)
    mc = float(max_c)
    s = float(scale)

    if invert_offsets:
        return ((mc - fc) / mc) * s
    else:
        return ((fc - mc) / mc) * s


def lerp(low, high, a):
    # linear interpolation of a (0.0-1.0) from low to high
    return (high-low) * a + low
