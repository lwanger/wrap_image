
"""
Create a 3D object of a height field of an image  wrapped around a cylinder (i.e. a height field in cylindrical
coordinates).

    TODO:
        - cutting edges (for cookie cutters)

    usage:
        python wrap_image.py -i image.png -o image.stl -ir 70.0 -or 80.0

        This will wrap image.png around a solid cylinder that is 70.0 millimeters for black pixels and 80 millimeters
        for white pixels. To add a hole, use the -hr command line option. Use -h to see other options.

Len Wanger
last updated: 2/15/2016

"""

import argparse
import numpy as np
import math
import collections
from PIL import Image
import pystl

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


def calc_vertices(im, inner_radius, outer_radius, z_scale, invert_offsets=False, reverse_x=False):
    vertices = np.zeros((im.width, im.height, 3), dtype=float)
    pi2 = math.pi * 2.0
    radians_per_pixel = pi2 / float(im.width)
    radius_diff = outer_radius - inner_radius
    width, height = im.width, im.height

    for i in range(width):
        for j in range(height):
            fi = float(i) if not reverse_x else float(width-i)
            fj = float(j)
            c_offset = calc_offset(im.getpixel((i, j)), 255.0, radius_diff, invert_offsets)
            x, y = cylindrical_coord((inner_radius + c_offset), (fi * radians_per_pixel))
            z = (fj)*z_scale
            vertices[i][j] = (x, y, z)

    return (vertices)


def draw_cylinder(stl, vertices, reverse_x=False):
    width, height, _ = vertices.shape

    for i in range(width-1):
        for j in range(height-1):
            v1 = (vertices[i][j][0], vertices[i][j][1], vertices[i][j][2])
            v2 = (vertices[i+1][j][0], vertices[i+1][j][1], vertices[i+1][j][2])
            v3 = (vertices[i+1][j+1][0], vertices[i+1][j+1][1], vertices[i+1][j+1][2])
            v4 = (vertices[i][j+1][0], vertices[i][j+1][1], vertices[i][j+1][2])

            if reverse_x:
                stl.add_quad(v4, v3, v2, v1)
            else:
                stl.add_quad(v1, v2, v3, v4)

    # add the seam (first to last)
    for j in range(height-1):
        v1 = (vertices[width-1][j][0], vertices[width-1][j][1], vertices[width-1][j][2])
        v2 = (vertices[0][j][0], vertices[0][j][1], vertices[0][j][2])
        v3 = (vertices[0][j+1][0], vertices[0][j+1][1], vertices[0][j+1][2])
        v4 = (vertices[width-1][j+1][0], vertices[width-1][j+1][1], vertices[width-1][j+1][2])

        if reverse_x:
            stl.add_quad(v4, v3, v2, v1)
        else:
            stl.add_quad(v1, v2, v3, v4)


def draw_end_cap_segment(stl, vertices, i1, i2, j, radians_per_pixel, reverse_x, add_hole, hole_radius, reverse_normal):
    if reverse_x:
        width, _, _ = vertices.shape
        fi1, fi2, fj = float(width-1-i1), float(width-1-i2), float(j)
    else:
        fi1, fi2, fj = float(i1), float(i2), float(j)

    v1 = vertices[i1][j]
    v2 = vertices[i2][j]

    if add_hole:
        x3 = hole_radius * math.cos((fi2) * radians_per_pixel)
        y3 = hole_radius * math.sin((fi2) * radians_per_pixel)
        x4 = hole_radius * math.cos((fi1) * radians_per_pixel)
        y4 = hole_radius * math.sin((fi1) * radians_per_pixel)

        v3 = Vertex3(x3, y3, fj*z_scale)
        v4 = Vertex3(x4, y4, fj*z_scale)

        #if reverse_normal:
        if reverse_x ^ reverse_normal:
            stl.add_quad(v1, v2, v3, v4)
        else:
            stl.add_quad(v4, v3, v2, v1)
    else:
        v3 = Vertex3(0.0, 0.0, fj*z_scale)

        if reverse_x ^ reverse_normal:
            t1 = Triangle(v1, v2, v3)
        else:
            t1 = Triangle(v1, v3, v2)

        stl.add_triangle(t1)


def draw_end_caps(stl, vertices, j, reverse_x, add_hole=False, reverse_normal=False):
    width, _, _ = vertices.shape
    pi2 = math.pi * 2.0
    radians_per_pixel = pi2 / float(width)
    for i in range(width-1):
        draw_end_cap_segment(stl, vertices, i, i+1, j, radians_per_pixel, reverse_x, add_hole, hole_radius, reverse_normal)

    # Draw from 0.0 to last
    draw_end_cap_segment(stl, vertices, width-1, 0.0, j, radians_per_pixel, reverse_x, add_hole, hole_radius, reverse_normal)


def draw_hole(stl, vertices, hole_radius, z_scale):
    width, height, _ = vertices.shape
    pi2 = math.pi * 2.0
    radians_per_pixel = pi2 / float(width)
    fj = float(height)

    for i in range(width-1):
        fi= float(i)

        x1 = (hole_radius) * math.cos(fi * radians_per_pixel)
        y1 = (hole_radius) * math.sin(fi * radians_per_pixel)
        x2 = (hole_radius) * math.cos((fi+1.0) * radians_per_pixel)
        y2 = (hole_radius) * math.sin((fi+1.0) * radians_per_pixel)

        v1 = Vertex3(x1, y1, 0.0)
        v2 = Vertex3(x2, y2, 0.0)
        v3 = Vertex3(x2, y2, fj*z_scale)
        v4 = Vertex3(x1, y1, fj*z_scale)

        stl.add_quad(v4, v3, v2, v1)

    # draw from last to first wedge
    x1 = (hole_radius) * math.cos((width-1.0) * radians_per_pixel)
    y1 = (hole_radius) * math.sin((width-1.0) * radians_per_pixel)
    x2 = (hole_radius) * math.cos((0.0) * radians_per_pixel)
    y2 = (hole_radius) * math.sin((0.0) * radians_per_pixel)

    v1 = Vertex3(x1, y1, 0.0)
    v2 = Vertex3(x2, y2, 0.0)
    v3 = Vertex3(x2, y2, fj*z_scale)
    v4 = Vertex3(x1, y1, fj*z_scale)

    stl.add_quad(v4, v3, v2, v1)


if __name__ == '__main__':
    # read arguments
    parser = argparse.ArgumentParser(description='Wrap an image around a cylinder')
    parser.add_argument('-i', '--image_file', nargs=1, help='Input image name')
    parser.add_argument('-o', '--output_file', nargs=1, help='Output STL file name')
    parser.add_argument('-ir', '--inner_radius', type=float, help='Radius of minimum image value (float)', default=70.0)
    parser.add_argument('-or', '--outer_radius', type=float, help='Radius of maximum image value (float)', default=80.0)
    parser.add_argument('-hr', '--hole_radius', type=float, help='Radius of hole (float - use negative for no hole)', default=-1.0)
    parser.add_argument('-z', '--z_scale', type=float, help='Scale value for Z height (float)', default=1.0)
    parser.add_argument('-rx', '--reverse_x', type=bool, help='Reverse the x axis (bool - i.e. scan clock verses counter-clockwise)', default=False)
    parser.add_argument('-iz', '--invert_offsets', type=bool, help='Invert offset (bool - i.e. darker colors in image stick out further)', default=False)
    parser.add_argument('-s', '--stl_type', type=str, help='STL file type - text or bin (default bin)', default='bin')
    args = parser.parse_args()

    img_name = args.image_file[0]
    stl_name = args.output_file[0]
    inner_radius = args.inner_radius
    outer_radius = args.outer_radius
    hole_radius = args.hole_radius
    z_scale = args.z_scale
    stl_type = 'txt' if args.stl_type[0]=='txt' else 'bin'
    add_hole  = True if hole_radius > 0.0 else False
    reverse_x = True if args.reverse_x else False
    invert_offsets = args.invert_offsets
    radius_diff = outer_radius - inner_radius

    print("Creating a cylindrical frieze for image={}, output={}".format(img_name, stl_name))

    convert_to = 'L'
    _ = Image.open(img_name)
    im = _.convert(convert_to)

    with pystl.PySTL(stl_name,  bin=True) as stl:
        vertices = calc_vertices(im, inner_radius, outer_radius, z_scale, invert_offsets=invert_offsets, reverse_x=reverse_x)
        draw_cylinder(stl, vertices, reverse_x)
        draw_end_caps(stl, vertices, 0.0, reverse_x, add_hole=add_hole)
        draw_end_caps(stl, vertices, im.height-1, reverse_x, add_hole=add_hole, reverse_normal=True)

        if add_hole:
           draw_hole(stl, vertices, hole_radius, z_scale)

    print("Frieze completed succesfully.")