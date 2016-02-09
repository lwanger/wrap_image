
"""
Create a cylindrical die for an image.

Todo:
    - OpenSCAD can't read binary STL (header issue?)
    - Convert to numpy
    - add cmd line options for file_name, stl_name, binary/txt

    global variables to set:
        img_name = string for input file image (e.g. 'output_001.bmp')
        stl_name = string for output STL file name (e.g. 'frieze.stl')
        inner_radius = inner radius for the cylinder (e.g. 50.0)
        outer_radius = outer radius for the cylinder - radius of maximum color in image (e.g. 55.0)
        z_scale = scale value for the Z direction (e.g. 1.0) for 1mm per pixel)
        invert_z = white is furthest out or black is (e.g. False)
        stl_type = text or binary STL file. Text files get very big~ (e.g. 'bin')

Len Wanger - 2/7/2016

"""

import math
import collections
from PIL import Image
import pystl

Vertex3 = collections.namedtuple('Vertex', 'x y z')
Triangle = collections.namedtuple('Triangle', 'v1 v2 v3')

#img_name = 'output_001.bmp'
img_name = 'freize1bw.jpg'
#img_name = 'freize2bw.jpg'
#img_name = 'freize3bw.jpg'


stl_name = 'frieze.stl'
inner_radius = 80.0
outer_radius = 86.0
z_scale=1.0

invert_z = False
#invert_z = True

radius_diff = outer_radius - inner_radius

#stl_type = 'txt'
stl_type = 'bin'


def make_triangle(d):
    """ Take a list of 3 points and return a Triangle """
    return Triangle(Vertex3(d[0][0], d[0][1], d[0][2]), Vertex3(d[1][0], d[1][1], d[1][2]), Vertex3(d[2][0], d[2][1], d[2][2]))


def cylindrical_coord(x, rads):
    x1 = x * math.cos(rads)
    y1 = x * math.sin(rads)
    return (x1, y1)


def calc_offset(c, max_c, scale, invert_z=False):
    fc = float(c)
    mc = float(max_c)
    s = float(scale)

    if invert_z:
        return ((mc - fc) / mc) * s
    else:
        return ((fc - mc) / mc) * s


def add_quad_to_stl(f, c1, c2, c3, c4, fi, fj, radians_per_pixel):
    c1_offset = calc_offset(c1, 255.0, radius_diff, invert_z)
    c2_offset = calc_offset(c2, 255.0, radius_diff, invert_z)
    c3_offset = calc_offset(c3, 255.0, radius_diff, invert_z)
    c4_offset = calc_offset(c4, 255.0, radius_diff, invert_z)

    x1, y1 = cylindrical_coord((inner_radius + c1_offset), (fi * radians_per_pixel))
    x2, y2 = cylindrical_coord((inner_radius + c2_offset), ((fi + 1.0) * radians_per_pixel))
    x3, y3 = cylindrical_coord((inner_radius + c3_offset), ((fi + 1.0) * radians_per_pixel))
    x4, y4 = cylindrical_coord((inner_radius + c4_offset), (fi * radians_per_pixel))
    v1 = Vertex3(x1, y1, (fj)*z_scale)
    v2 = Vertex3(x2, y2, (fj)*z_scale)
    v3 = Vertex3(x3, y3, (fj + 1.0)*z_scale)
    v4 = Vertex3(x4, y4, (fj + 1.0)*z_scale)
    t1 = Triangle(v1, v2, v4)
    t2 = Triangle(v2, v3, v4)

    if stl_type == 'txt':
        pystl.write_stl_triangle(f, t1)
        pystl.write_stl_triangle(f, t2)
    else:
        pystl.write_stl_bin_triangle(f, t1)
        pystl.write_stl_bin_triangle(f, t2)


def draw_cylinder(f, im):
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
            add_quad_to_stl(f, c1, c2, c3, c4, fi, fj, radians_per_pixel)

    # add the seam (first to last)
    fi = float(im.width-1)
    for j in range(im.height-1):
        fj = float(j)
        c1 = im.getpixel((im.width-1, j))
        c2 = im.getpixel((0, j))
        c3 = im.getpixel((0, j+1))
        c4 = im.getpixel((im.width-1, j+1))
        add_quad_to_stl(f, c1, c2, c3, c4, fi, fj, radians_per_pixel)


def draw_end_caps(f, im, j, reverse_normal=False):
    pi2 = math.pi * 2.0
    radians_per_pixel = pi2 / float(im.width)
    radius_diff = outer_radius - inner_radius

    fj = float(j)

    for i in range(im.width-1):
        fi= float(i)
        c1 = im.getpixel((i,0))
        c2 = im.getpixel((i+1,0))
        # c1_offset = ((float(c1)-255.0)/255.0) * radius_diff
        # c2_offset = ((float(c2)-255.0)/255.0) * radius_diff

        c1_offset = calc_offset(c1, 255.0, radius_diff, invert_z)
        c2_offset = calc_offset(c2, 255.0, radius_diff, invert_z)

        x1 = (inner_radius + c1_offset) * math.cos(fi * radians_per_pixel)
        y1 = (inner_radius + c1_offset) * math.sin(fi * radians_per_pixel)
        x2 = (inner_radius + c2_offset) * math.cos((fi + 1.0) * radians_per_pixel)
        y2 = (inner_radius + c2_offset) * math.sin((fi + 1.0) * radians_per_pixel)

        v1 = Vertex3(x1, y1, fj*z_scale)
        v2 = Vertex3(x2, y2, fj*z_scale)
        v3 = Vertex3(0.0, 0.0, fj*z_scale)
        #t1 = Triangle(v1, v2, v3)

        if reverse_normal:
            t1 = Triangle(v1, v2, v3)
        else:
            t1 = Triangle(v1, v3, v2)

        if stl_type == 'txt':
            pystl.write_stl_triangle(f, t1)
        else:
            pystl.write_stl_bin_triangle(f, t1)

    # draw from last to first wedge
    fi = float(im.width-1)
    c1 = im.getpixel((im.width-1,0))
    c2 = im.getpixel((0,0))
    # c1_offset = ((float(c1)-255.0)/255.0) * radius_diff
    # c2_offset = ((float(c2)-255.0)/255.0) * radius_diff

    c1_offset = calc_offset(c1, 255.0, radius_diff, invert_z)
    c2_offset = calc_offset(c2, 255.0, radius_diff, invert_z)

    x1 = (inner_radius + c1_offset) * math.cos(fi * radians_per_pixel)
    y1 = (inner_radius + c1_offset) * math.sin(fi * radians_per_pixel)
    x2 = (inner_radius + c2_offset) * math.cos((0.0) * radians_per_pixel)
    y2 = (inner_radius + c2_offset) * math.sin((0.0) * radians_per_pixel)
    v1 = Vertex3(x1, y1, fj*z_scale)
    v2 = Vertex3(x2, y2, fj*z_scale)
    v3 = Vertex3(0.0, 0.0, fj*z_scale)
    t1 = Triangle(v1, v2, v3)
    n = (0.0, 0.0, 1.0)
    if stl_type == 'txt':
        pystl.write_stl_triangle(f, t1, n)
    else:
        pystl.write_stl_bin_triangle(f, t1, n)

if __name__ == '__main__':
    print("starting")
    convert_to = 'L'
    _ = Image.open(img_name)
    im = _.convert(convert_to)

    if stl_type == 'txt':
        f = open(stl_name, 'w')
        pystl.write_stl_header(f)
    else:
        f = open(stl_name, 'wb')
        num_triangles = (im.width*(im.height-1)*2) + (im.width * 2)
        pystl.write_stl_bin_header(f, num_triangles)

    draw_cylinder(f, im)
    draw_end_caps(f, im, 0.0)
    draw_end_caps(f, im, im.height, reverse_normal=True)

    if stl_type == 'txt':
            pystl.write_stl_trailer(f)

    f.close()
    print("done")
