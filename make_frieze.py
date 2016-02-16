
"""
Create a cylindrical die for an image.

- IO on image
- deeper pattern
- cutting edges


Todo:
    - clean up code
        - pre-calculate all offsets.
        - create vertex list
        - Get rid of global variables

    global variables to set:
        img_name = string for input file image (e.g. 'output_001.bmp')
        stl_name = string for output STL file name (e.g. 'frieze.stl')
        inner_radius = inner radius for the cylinder (e.g. 50.0)
        outer_radius = outer radius for the cylinder - radius of maximum color in image (e.g. 55.0)
        z_scale = scale value for the Z direction (e.g. 1.0) for 1mm per pixel)
        invert_offsets = white is furthest out or black is (e.g. False)
        stl_type = text or binary STL file. Text files get very big~ (e.g. 'bin')

Len Wanger - 2/15/2016

"""

import argparse
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


def draw_pixel_box(stl, c1, c2, c3, c4, fi, fj, radians_per_pixel):
    c1_offset = calc_offset(c1, 255.0, radius_diff, invert_offsets)
    c2_offset = calc_offset(c2, 255.0, radius_diff, invert_offsets)
    c3_offset = calc_offset(c3, 255.0, radius_diff, invert_offsets)
    c4_offset = calc_offset(c4, 255.0, radius_diff, invert_offsets)

    x1, y1 = cylindrical_coord((inner_radius + c1_offset), (fi * radians_per_pixel))
    x2, y2 = cylindrical_coord((inner_radius + c2_offset), ((fi + 1.0) * radians_per_pixel))
    x3, y3 = cylindrical_coord((inner_radius + c3_offset), ((fi + 1.0) * radians_per_pixel))
    x4, y4 = cylindrical_coord((inner_radius + c4_offset), (fi * radians_per_pixel))
    v1 = Vertex3(x1, y1, (fj)*z_scale)
    v2 = Vertex3(x2, y2, (fj)*z_scale)
    v3 = Vertex3(x3, y3, (fj + 1.0)*z_scale)
    v4 = Vertex3(x4, y4, (fj + 1.0)*z_scale)

    stl.add_quad(v1, v2, v3, v4)


def draw_cylinder(stl, im):
    pi2 = math.pi * 2.0
    radians_per_pixel = pi2 / float(im.width)

    for i in range(im.width-1):
        for j in range(im.height-1):
            fi = float(i)
            fj = float(j)

            c1 = im.getpixel((i, j))
            c2 = im.getpixel((i+1, j))
            c3 = im.getpixel((i+1, j+1))
            c4 = im.getpixel((i, j+1))
            draw_pixel_box(stl, c1, c2, c3, c4, fi, fj, radians_per_pixel)

    # add the seam (first to last)
    fi = float(im.width-1)
    for j in range(im.height-1):
        fj = float(j)
        c1 = im.getpixel((im.width-1, j))
        c2 = im.getpixel((0, j))
        c3 = im.getpixel((0, j+1))
        c4 = im.getpixel((im.width-1, j+1))
        draw_pixel_box(stl, c1, c2, c3, c4, fi, fj, radians_per_pixel)


def draw_end_cap_segment(stl, im, i1, i2, fj, radians_per_pixel, add_hole, reverse_normal):
    fi1= float(i1)
    fi2= float(i2)

    c1 = im.getpixel((i1,0))
    c2 = im.getpixel((i2,0))

    c1_offset = calc_offset(c1, 255.0, radius_diff, invert_offsets)
    c2_offset = calc_offset(c2, 255.0, radius_diff, invert_offsets)

    x1 = (inner_radius + c1_offset) * math.cos(fi1 * radians_per_pixel)
    y1 = (inner_radius + c1_offset) * math.sin(fi1 * radians_per_pixel)
    x2 = (inner_radius + c2_offset) * math.cos((fi2) * radians_per_pixel)
    y2 = (inner_radius + c2_offset) * math.sin((fi2) * radians_per_pixel)

    v1 = Vertex3(x1, y1, fj*z_scale)
    v2 = Vertex3(x2, y2, fj*z_scale)

    if add_hole:
        x3 = hole_radius * math.cos((fi2) * radians_per_pixel)
        y3 = hole_radius * math.sin((fi2) * radians_per_pixel)
        x4 = hole_radius * math.cos((fi1) * radians_per_pixel)
        y4 = hole_radius * math.sin((fi1) * radians_per_pixel)

        v3 = Vertex3(x3, y3, fj*z_scale)
        v4 = Vertex3(x4, y4, fj*z_scale)

        if reverse_normal:
            stl.add_quad(v1, v2, v3, v4)
        else:
            stl.add_quad(v4, v3, v2, v1)
    else:
        v3 = Vertex3(0.0, 0.0, fj*z_scale)

        if reverse_normal:
            t1 = Triangle(v1, v2, v3)
        else:
            t1 = Triangle(v1, v3, v2)

        stl.add_triangle(t1)




def draw_end_caps(stl, im, j, add_hole=False, reverse_normal=False):
    pi2 = math.pi * 2.0
    radians_per_pixel = pi2 / float(im.width)
    #radius_diff = outer_radius - inner_radius

    fj = float(j)

    for i in range(im.width-1):
        draw_end_cap_segment(stl, im, i, i+1, fj, radians_per_pixel, add_hole, reverse_normal)

    # Draw from 0.0 to last
    draw_end_cap_segment(stl, im, im.width-1, 0.0, fj, radians_per_pixel, add_hole, reverse_normal)


def draw_hole(stl, im, j):
    pi2 = math.pi * 2.0
    radians_per_pixel = pi2 / float(im.width)

    fj = float(j)

    for i in range(im.width-1):
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
    x1 = (hole_radius) * math.cos((im.width-1.0) * radians_per_pixel)
    y1 = (hole_radius) * math.sin((im.width-1.0) * radians_per_pixel)
    x2 = (hole_radius) * math.cos((0.0) * radians_per_pixel)
    y2 = (hole_radius) * math.sin((0.0) * radians_per_pixel)

    v1 = Vertex3(x1, y1, 0.0)
    v2 = Vertex3(x2, y2, 0.0)
    v3 = Vertex3(x2, y2, fj*z_scale)
    v4 = Vertex3(x1, y1, fj*z_scale)

    stl.add_quad(v4, v3, v2, v1)

if __name__ == '__main__':
    print("starting")

    # read arguments
    parser = argparse.ArgumentParser(description='Wrap an image around a cylinder')
    parser.add_argument('-i', '--image_file', nargs=1, help='Input image name')
    parser.add_argument('-o', '--output_file', nargs=1, help='Output STL file name')
    parser.add_argument('-ir', '--inner_radius', type=float, help='Radius of minimum image value (float)', default=70.0)
    parser.add_argument('-or', '--outer_radius', type=float, help='Radius of maximum image value (float)', default=80.0)
    parser.add_argument('-hr', '--hole_radius', type=float, help='Radius of hole (float - use negative for no hole)', default=-1.0)
    parser.add_argument('-z', '--z_scale', type=float, help='Scale value for Z height (float)', default=1.0)
    parser.add_argument('-iz', '--invert_offsets', type=bool, help='Invert offset (bool - i.e. darker colors in image stick out further)', default=False)
    parser.add_argument('-s', '--stl_type', type=str, help='STL file type - text or bin (default bin)', default='bin')

    args = parser.parse_args()
    print(args)

    img_name = args.image_file[0]
    stl_name = args.output_file[0]
    inner_radius = args.inner_radius
    outer_radius = args.outer_radius
    hole_radius = args.hole_radius
    z_scale = args.z_scale
    stl_type = 'txt' if args.stl_type[0]=='txt' else 'bin'
    add_hole  = True if hole_radius > 0.0 else False
    invert_offsets = args.invert_offsets
    radius_diff = outer_radius - inner_radius

    convert_to = 'L'
    _ = Image.open(img_name)
    im = _.convert(convert_to)

    with pystl.PySTL(stl_name,  bin=True) as stl:
        draw_cylinder(stl, im)
        draw_end_caps(stl, im, 0.0, add_hole=add_hole)
        draw_end_caps(stl, im, im.height, add_hole=add_hole, reverse_normal=True)

        if add_hole:
            draw_hole(stl, im, im.height)

    print("done")