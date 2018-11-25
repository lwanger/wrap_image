
"""
Create a 3D object of a height field of an image  on the face of a cylinder.

    TODO:
        - can't open in netfabb (opens in meshlab and paint3d). Problems in meshmixer. Asks to unify duplicated
            vertices in meshlab

    usage:
        python stamp_image.py -i image.png -o image.stl

        options:

            --margin - Margin around the image (percentage 1.0-100.0)
            --image_low - Low Z value for the stamp Z height (float)
            --image_high - High Z value for the stamp Z height (float)
            --invert_image - Invert the image (bool - i.e. darker colors in image stick out further)
            --mirror_image - Mirror the image
            --outer_radius - Radius of the cylinder (float)
            --roundness - roundness of the cylinder (int)
            --z_height - height of the cylinder for the stamp
            --stl_type - STL file type - text or bin (default bin)

        The options are somewhat confusing as the stamp goes on the bottom (Z=0.0) so by default the stamp goes from
        image_low of 0.0 to image_high of -4.0 (4 mm below the bottom).

    To test try:

        python stamp_image.py -i test_image.png -i test_image.png -o stamp.stl

        this is by default with: margin=1.0, invert_image=True, mirror_image=True, image_low=0.0, image_high=-4.0,
            outer_radius=20.0, roundness=6, z_height=70.0

        You cna play with other options too:

        -or- inset

        python stamp_image.py -i test_image.png --margin=5.0 --image_low=5.0 --image_high=10.0 -o stamp.stl -or=40.0 -z=60.0 --roundness=4

        -or- inverted image:

        python stamp_image.py -i test_image.png --margin=5.0 --image_low=5.0 --image_high=10.0 -o stamp.stl -or=40.0 -z=60.0 --roundness=4 --invert_image=true

        -or- mirrored image:

        python stamp_image.py -i test_image.png --margin=5.0 --image_low=5.0 --image_high=10.0 -o stamp.stl -or=40.0 -z=60.0 --roundness=4 --mirror_image=true

        -or- set image_high to 0.0 to make the stamp flush with the bottom:

        python stamp_image.py -i test_image.png --margin=5.0 --image_low=0.0 --image_high=10.0 -o stamp.stl -or=70.0 -z=40.0 --roundness=4

        -or- set image_low to 0.0 and invert the image to make the stamp flush with the bottom but inset:

        python stamp_image.py -i test_image.png --margin=5.0 --image_low=0.0 --image_high=10.0 -o stamp.stl -or=70.0 -z=40.0 --roundness=4 --invert_image=true

Len Wanger
last updated: 2018

"""

import argparse
import numpy as np
import math
from PIL import Image
import pystl
import sys

from utils import Vertex3, Triangle


def calc_max_xy(im_width, im_height, outer_radius, margin_pct):
    inner_radius = (100.0 - margin_pct)/100.0 * outer_radius
    hypot = math.sqrt(im_width ** 2 + im_height ** 2)
    scale = inner_radius / hypot
    max_x = im_width * scale
    max_y = im_height * scale
    return max_x, max_y


def calc_stamp_vertices(im, outer_radius, margin_pct, low_z, high_z, mirror_image=False, invert_image=False):
    """
    center of image is at (0,0)
    assume pixels are square. Calculate the size of pixels (pixel_width in each dimension)
    The stamp fits in a circle (cap of a cylinder) with radius of outer_radius. Margin percentage is the blank space
    from the edge of the circle to the edge of the image. The width of the margin on each side is: outer_radius * (1-margin_pct)
    The margin is based on the hypotenus of the triangle from the origin to (im_width,0( and (im_width, im_height).
    """
    im_width, im_height = im.width, im.height
    vertices = np.zeros((im_width, im_height, 3), dtype=float)
    max_x, max_y = calc_max_xy(im_width, im_height, outer_radius, margin_pct)

    min_x = -max_x
    min_y = -max_y
    wm1 = im_width - 1
    hm1 = im_height - 1
    delta_z = high_z - low_z
    delta_x = max_x - min_x
    delta_y = max_y - min_y

    for i in range(im_width):
        for j in range(im_height):
            i_idx = i if mirror_image == False else wm1-i
            x = (delta_x * (i / wm1)) + min_x
            y = (delta_y * (j / hm1)) + min_y
            pixel_val = im.getpixel((i_idx, j))

            if invert_image is True:
                z_a = (255.0 - pixel_val) / 255.0
            else:
                z_a = pixel_val / 255.0

            z = (delta_z * z_a) + low_z # lerp(cap_z, high_z, z_a)
            vertices[i][j] = (x, y, z)

    return vertices


def draw_stamp(stl, vertices, reverse_direction=False):
    width, height, _ = vertices.shape

    for i in range(width-1):
        for j in range(height-1):
            z = vertices[i][j][2]
            z_next_x = vertices[i+1][j][2]
            z_next_y = vertices[i][j+1][2]

            v1 = (vertices[i][j][0], vertices[i][j][1], z)
            v2 = (vertices[i+1][j][0], vertices[i+1][j][1], z)
            v3 = (vertices[i+1][j+1][0], vertices[i+1][j+1][1], z)
            v4 = (vertices[i][j+1][0], vertices[i][j+1][1], z)

            if reverse_direction:
                stl.add_quad(v1, v2, v3, v4)
            else:
                stl.add_quad(v4, v3, v2, v1)

            # draw sidewall to next pixel over
            if z != z_next_x:
                v1 = (vertices[i+1][j][0], vertices[i+1][j][1], z)
                v2 = (vertices[i+1][j][0], vertices[i+1][j][1], z_next_x)
                v3 = (vertices[i+1][j+1][0], vertices[i+1][j+1][1], z_next_x)
                v4 = (vertices[i+1][j+1][0], vertices[i+1][j+1][1], z)
                stl.add_quad(v4, v3, v2, v1)

            # draw sidewall to next pixel down
            if z != z_next_y:
                v1 = (vertices[i][j+1][0], vertices[i][j+1][1], z)
                v2 = (vertices[i+1][j+1][0], vertices[i+1][j+1][1], z)
                v3 = (vertices[i+1][j+1][0], vertices[i+1][j+1][1], z_next_y)
                v4 = (vertices[i][j+1][0], vertices[i][j+1][1], z_next_y)
                stl.add_quad(v4, v3, v2, v1)


def draw_margin(stl, im, radius, margin_pct, z, segments=20):
    """
    # Draw the cap of the cylinder. cemtered at (0,0). Since there is a square hole in the middle of the cap
    it's a little confusing. It's drawn as quandrants (segments/4) pieces. The first and the last segments of
    the quadrant are drawn as quads to the corner and halfway along the closest edge. The rest as triangles.
    """
    max_x, max_y = calc_max_xy(im.width, im.height, outer_radius, margin_pct)
    qtr_segments = segments // 4
    pi2 = math.pi * 2.0

    # draw 1st quadrant
    for i in range(qtr_segments):
        start = (i / segments) * pi2
        stop = ((i+1) / segments) * pi2
        start_x = math.cos(start) * radius
        start_y = math.sin(start) * radius
        stop_x = math.cos(stop) * radius
        stop_y = math.sin(stop) * radius
        v1 = Vertex3(start_x, start_y, z)
        v2 = Vertex3(stop_x, stop_y, z)

        if i==0:    # draw a quad to corner
            v3 = Vertex3(max_x, max_y, z)
            v4 = Vertex3(max_x, 0.0, z)
            stl.add_quad(v4,v3,v2,v1)
        elif i == (qtr_segments-1):
            v3 = Vertex3(0.0, max_y, z)
            v4 = Vertex3(max_x, max_y, z)
            stl.add_quad(v4,v3,v2,v1)
        else:
            v3 = Vertex3(max_x, max_y, z)
            tri = Triangle(v3, v2, v1)
            stl.add_triangle(tri)

    # draw 2nd quadrant
    for i in range(qtr_segments, 2*qtr_segments):
        start = (i / segments) * pi2
        stop = ((i + 1) / segments) * pi2
        start_x = math.cos(start) * radius
        start_y = math.sin(start) * radius
        stop_x = math.cos(stop) * radius
        stop_y = math.sin(stop) * radius
        v1 = Vertex3(start_x, start_y, z)
        v2 = Vertex3(stop_x, stop_y, z)

        if i==qtr_segments:    # draw a quad to corner
            v3 = Vertex3(-max_x, max_y, z)
            v4 = Vertex3(0.0, max_y, z)
            stl.add_quad(v4,v3,v2,v1)
        elif i == (2*qtr_segments-1):
            v3 = Vertex3(-max_x, 0.0, z)
            v4 = Vertex3(-max_x, max_y, z)
            stl.add_quad(v4,v3,v2,v1)
        else:
            v3 = Vertex3(-max_x, max_y, z)
            tri = Triangle(v3, v2, v1)
            stl.add_triangle(tri)

    # draw 3rd quadrant
    for i in range(2*qtr_segments, 3*qtr_segments):
        start = (i / segments) * pi2
        stop = ((i + 1) / segments) * pi2
        start_x = math.cos(start) * radius
        start_y = math.sin(start) * radius
        stop_x = math.cos(stop) * radius
        stop_y = math.sin(stop) * radius
        v1 = Vertex3(start_x, start_y, z)
        v2 = Vertex3(stop_x, stop_y, z)

        if i==2*qtr_segments:    # draw a quad to corner
            v3 = Vertex3(-max_x, -max_y, z)
            v4 = Vertex3(-max_x, 0.0, z)
            stl.add_quad(v4,v3,v2,v1)
        elif i == (3*qtr_segments-1):
            v3 = Vertex3(0.0, -max_y, z)
            v4 = Vertex3(-max_x, -max_y, z)
            stl.add_quad(v4,v3,v2,v1)
        else:
            v3 = Vertex3(-max_x, -max_y, z)
            tri = Triangle(v3, v2, v1)
            stl.add_triangle(tri)

    for i in range(3*qtr_segments, segments):
        start = (i / segments) * pi2
        stop = ((i + 1) / segments) * pi2
        start_x = math.cos(start) * radius
        start_y = math.sin(start) * radius
        stop_x = math.cos(stop) * radius
        stop_y = math.sin(stop) * radius
        v1 = Vertex3(start_x, start_y, z)
        v2 = Vertex3(stop_x, stop_y, z)

        if i==3*qtr_segments:    # draw a quad to corner
            v3 = Vertex3(max_x, -max_y, z)
            v4 = Vertex3(0.0, -max_y, z)
            stl.add_quad(v4,v3,v2,v1)
        elif i == (segments-1):
            v3 = Vertex3(max_x, 0.0, z)
            v4 = Vertex3(max_x, -max_y, z)
            stl.add_quad(v4,v3,v2,v1)
        else:
            v3 = Vertex3(max_x, -max_y, z)
            tri = Triangle(v3, v2, v1)
            stl.add_triangle(tri)


def draw_hollow_cylinder(stl, radius, bottom_z, top_z, segments=20):
    pi2 = math.pi * 2.0
    for i in range(segments):
        start = (i / segments) * pi2
        stop = ((i+1) / segments) * pi2

        start_x = math.cos(start) * radius
        start_y = math.sin(start) * radius
        stop_x = math.cos(stop) * radius
        stop_y = math.sin(stop) * radius

        v1 = Vertex3(start_x, start_y, bottom_z)
        v2 = Vertex3(stop_x, stop_y, bottom_z)
        v3 = Vertex3(stop_x, stop_y, top_z)
        v4 = Vertex3(start_x, start_y, top_z)
        stl.add_quad(v1, v2, v3, v4)


def draw_cylinder_cap(stl, radius, z, segments=20):
    # Draw the cap of the cylinder. cemtered at (0,0)
    pi2 = math.pi * 2.0
    for i in range(segments):
        start = (i / segments) * pi2
        stop = ((i + 1) / segments) * pi2
        start_x = math.cos(start) * radius
        start_y = math.sin(start) * radius
        stop_x = math.cos(stop) * radius
        stop_y = math.sin(stop) * radius
        v1 = Vertex3(start_x, start_y, z)
        v2 = Vertex3(stop_x, stop_y, z)
        v3 = Vertex3(0.0, 0.0, z)
        tri = Triangle(v1, v2, v3)
        stl.add_triangle(tri)


def draw_sidewalls(stl, vertices, outer_radius, margin_pct, z):
    # draw walls from the edges of the image to the stamp plane (bottom or top)
    width, height = im.width, im.height
    max_x, max_y = calc_max_xy(width, height, outer_radius, margin_pct)

    wm1 = width - 1
    hm1 = height - 1

    for x in range(wm1):
        v1 = Vertex3(vertices[x][0][0], -max_y, z)
        v2 = Vertex3(vertices[x+1][0][0], -max_y, z)
        v3 = Vertex3(vertices[x+1][0][0], -max_y, vertices[x+1][0][2])
        v4 = Vertex3(vertices[x][0][0], -max_y, vertices[x][0][2])
        stl.add_quad(v4, v3, v2, v1)

        v1 = Vertex3(vertices[x][hm1][0], max_y, z)
        v2 = Vertex3(vertices[x+1][hm1][0], max_y, z)
        v3 = Vertex3(vertices[x+1][hm1][0], max_y, vertices[x+1][hm1][2])
        v4 = Vertex3(vertices[x][hm1][0], max_y, vertices[x][hm1][2])
        stl.add_quad(v1, v2, v3, v4)

    for y in range(hm1):
        v1 = Vertex3(-max_x, vertices[0][y][1], z)
        v2 = Vertex3(-max_x, vertices[0][y+1][1], z)
        v3 = Vertex3(-max_x, vertices[0][y+1][1], vertices[0][y+1][2])
        v4 = Vertex3(-max_x, vertices[0][y][1], vertices[0][y][2])
        stl.add_quad(v1, v2, v3, v4)

        v1 = Vertex3(max_x, vertices[wm1][y][1], z)
        v2 = Vertex3(max_x, vertices[wm1][y + 1][1], z)
        v3 = Vertex3(max_x, vertices[wm1][y + 1][1], vertices[wm1][y + 1][2])
        v4 = Vertex3(max_x, vertices[wm1][y][1], vertices[wm1][y][2])
        stl.add_quad(v4, v3, v2, v1)


if __name__ == '__main__':
    # read arguments
    parser = argparse.ArgumentParser(description='Wrap an image around a cylinder')
    parser.add_argument('-i', '--image_file', nargs=1, help='Input image name', required=True)
    parser.add_argument('-o', '--output_file', nargs=1, help='Output STL file name', required=True)
    parser.add_argument('-m', '--margin', type=float, help='Margin around the image (percentage)', default=1.0)
    parser.add_argument('-il', '--image_low', type=float, help='Low Z value for the stamp Z height (float)', default=0.0)
    parser.add_argument('-ih', '--image_high', type=float, help='High Z value for the stamp Z height (float)', default=-4.0)
    parser.add_argument('-ii', '--invert_image', type=bool, help='Invert the image (bool - i.e. darker colors in image stick out further)', default=True)
    parser.add_argument('-mi', '--mirror_image', type=bool, help='Mirror the image', default=True)
    parser.add_argument('-or', '--outer_radius', type=float, help='Radius of the cylinder (float)', default=20.0)
    parser.add_argument('-r', '--roundness', type=int, help='roundness of the cylinder (int)', default=6)
    parser.add_argument('-z', '--z_height', type=float, help='height of the cylinder for the stamp', default=70.0)
    parser.add_argument('-s', '--stl_type', type=str, help='STL file type - text or bin (default bin)', default='bin')
    args = parser.parse_args()

    image_name = args.image_file[0]
    stl_name = args.output_file[0]
    margin = args.margin
    invert_image = args.invert_image
    mirror_image = True if args.mirror_image else False
    low_z = args.image_low
    high_z = args.image_high
    roundness = args.roundness
    outer_radius = args.outer_radius
    z_height = args.z_height
    stl_type = 'txt' if args.stl_type[0]=='txt' else 'bin'

    # validate parameters...
    if margin < 0.0 or margin > 100.0:
        print("Bottom margin is a percentage between 0.0 and 100.0")
        sys.exit(1)

    if roundness < 1 or roundness > 50:
        print("Roundness is an integer between 1 and 50")
        sys.exit(1)

    options = []

    if mirror_image is True:
        options.append('mirrored')

    if invert_image is True:
        options.append('inverted')

    if len(options):
        option_str = '({})'.format(', '.join(options))
    else:
        option_str = ''

    print("Creating an image stamp for image={}, output={} {}".format(image_name, stl_name, option_str))

    segments = (roundness + 2) * 4
    convert_to = 'L'
    bot_img_file = Image.open(image_name)
    im = bot_img_file.convert(convert_to)

    with pystl.PySTL(stl_name,  bin=True) as stl:
        # create geometry for the bottom image cap
        vertices = calc_stamp_vertices(im, outer_radius, margin, low_z, high_z, mirror_image, invert_image)
        draw_stamp(stl, vertices)

        # draw blank area around the stamp
        draw_margin(stl, im, outer_radius, margin, 0.0, segments=segments)
        draw_sidewalls(stl, vertices, outer_radius, margin, 0.0)

        # create geometry for the cylinder sides
        draw_hollow_cylinder(stl, outer_radius, 0.0, top_z=z_height, segments=segments)

        # draw top cap
        draw_cylinder_cap(stl, outer_radius,z_height, segments=segments)


    print("Frieze completed succesfully.")