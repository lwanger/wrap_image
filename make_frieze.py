
"""
Create a cylindrical die for an image.

Todo:

- Write a binary STL file
- Why the numerical error in the triangles?
- Add height based on image value
- Test in OpenSCAD

Len Wanger - 2/7/2016

"""

import math
import collections
from PIL import Image
import pystl

Vertex3 = collections.namedtuple('Vertex', 'x y z')
Triangle = collections.namedtuple('Triangle', 'v1 v2 v3')

img_name = 'face2.png'
stl_name = 'frieze.stl'
inner_radius = 50.0
outer_radius = 55.0


def make_triangle(d):
    """ Take a list of 3 points and return a Triangle """
    return Triangle(Vertex3(d[0][0], d[0][1], d[0][2]), Vertex3(d[1][0], d[1][1], d[1][2]), Vertex3(d[2][0], d[2][1], d[2][2]))


def cylindrical_coord(x, y, rads):
    x1 = x * math.cos(rads)
    y1 = y * math.sin(rads)
    return (x1, y1)

def draw_cylinder(f, im):
    pi2 = math.pi * 2.0
    radians_per_pixel = pi2 / float(im.width)
    radius_diff = outer_radius - inner_radius

    for i in range(im.width-1):
        for j in range(im.height-1):
            fi, fj = float(i), float(j)
            fi2, fj2 = float(i+1), float(j+1)

            c1 = im.getpixel((i,j))
            c2 = im.getpixel((i+1,j))
            c3 = im.getpixel((i+1,j+1))
            c4 = im.getpixel((i,j+1))

            c1_offset = ((float(c1)-255.0)/255.0) * radius_diff
            c2_offset = ((float(c2)-255.0)/255.0) * radius_diff
            c3_offset = ((float(c3)-255.0)/255.0) * radius_diff
            c4_offset = ((float(c4)-255.0)/255.0) * radius_diff

            # x1 = (inner_radius + c1_offset) * math.cos(fi * radians_per_pixel)
            # y1 = (inner_radius + c2_offset) * math.sin(fi * radians_per_pixel)
            # x2 = (inner_radius + c3_offset) * math.cos((fi + 1.0) * radians_per_pixel)
            # y2 = (inner_radius + c4_offset) * math.sin((fi + 1.0) * radians_per_pixel)

            x1, y1 = cylindrical_coord((inner_radius + c1_offset), (inner_radius + c1_offset), (fi * radians_per_pixel))
            x2, y2 = cylindrical_coord((inner_radius + c2_offset), (inner_radius + c2_offset), ((fi+1.0) * radians_per_pixel))
            x3, y3 = cylindrical_coord((inner_radius + c3_offset), (inner_radius + c2_offset), ((fi+1.0) * radians_per_pixel))
            x4, y4 = cylindrical_coord((inner_radius + c1_offset), (inner_radius + c1_offset), (fi * radians_per_pixel))

            # v1 = Vertex3(x1, y1, fj)
            # v2 = Vertex3(x2, y1, fj)
            # v3 = Vertex3(x2, y2, fj+1.0)
            # v4 = Vertex3(x1, y2, fj+1.0)
            v1 = Vertex3(x1, y1, fj)
            v2 = Vertex3(x2, y2, fj)
            v3 = Vertex3(x3, y3, fj+1.0)
            v4 = Vertex3(x4, y4, fj+1.0)

            t1 = Triangle(v1, v2, v4)
            t2 = Triangle(v2, v3, v4)

            pystl.write_stl_triangle(f, t1)
            pystl.write_stl_triangle(f, t2)


def draw_end_caps(f, im):
    pi2 = math.pi * 2.0
    radians_per_pixel = pi2 / float(im.width)
    radius_diff = outer_radius - inner_radius

    j = 0.0
    #j = float(im.height)

    for i in range(im.width-1):
        fi, fj = float(i), float(j)
        c1 = im.getpixel((i,0))
        c2 = im.getpixel((i+1,0))
        c1_offset = ((float(c1)-255.0)/255.0) * radius_diff
        c2_offset = ((float(c2)-255.0)/255.0) * radius_diff
        x1 = (inner_radius + c1_offset) * math.cos(fi * radians_per_pixel)
        y1 = (inner_radius + c1_offset) * math.sin(fi * radians_per_pixel)
        x2 = (inner_radius + c2_offset) * math.cos((fi + 1.0) * radians_per_pixel)
        y2 = (inner_radius + c2_offset) * math.sin((fi + 1.0) * radians_per_pixel)

        v1 = Vertex3(x1, y1, fj)
        v2 = Vertex3(x2, y2, fj)
        v3 = Vertex3(0.0, 0.0, fj)
        t1 = Triangle(v1, v2, v3)

        pystl.write_stl_triangle(f, t1)

    pystl.write_stl_triangle(f, t1)

if __name__ == '__main__':
    convert_to = 'L'

    _ = Image.open(img_name)
    im = _.convert(convert_to)
    print('im_size: {}, {}'.format(im.width, im.height))

    # pi2 = math.pi * 2.0
    # radians_per_pixel = pi2 / float(im.width)
    # radius_diff = outer_radius - inner_radius

    with open(stl_name, 'w') as f:
        pystl.write_stl_header(f)

        draw_cylinder(f, im)
        draw_end_caps(f, im)

        pystl.write_stl_trailer(f)

