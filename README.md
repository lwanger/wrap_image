Two programs to create 3D cookie/clay tools.

# wrap_image
Python program to wrap the height field of an image around a cylinder and save the output as an STL file.

usage:
        python wrap_image.py -i freize1.jpg -o freize1.stl -ir 70.0 -or 80.0 -hr 40.0

        This will wrap image.png around a solid cylinder that is 70.0 millimeters for black pixels and 80 millimeters
        for white pixels, with a 40 millimeter hole in the middle. Use -h to see all the available options.

# stamp_image 
Python program to create a stamp (image on the bottom face of the cylinder).

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

Len Wanger
last updated: 1/25/2018
