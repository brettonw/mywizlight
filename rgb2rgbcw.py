#!/usr/bin/env python3

import math;
import operator;

from pywizlight.bulb import PilotBuilder, PilotParser, wizlight

from vec import *;

# can't actually change a value like this from another files once it's been loaded. this
# is actually a very bad design on python's part IMNSHO, and this is an ugly workaround
verbose = [False];
def setVerbose (val):
    verbose[0] = val;

# red, green, blue basis vectors to simulate the homekit color wheel - just vectors at 3
# angles (0, 120, 240)
angle = (math.pi * 2) / 3;
basis = (
    vecFromAngle (0),
    vecFromAngle (angle),
    vecFromAngle (angle * 2)
);

def printBasis (basis, prefix = ""):
    if verbose[0]:
        print ("{}Basis Vectors: ".format (prefix), end = "");
        for vector in basis:
            print ("{} ".format (vecFormat (vector)), end="");
        print ("");
printBasis (basis);

def rgb2rgbcw (rgb):
    # in the homekit color wheel, red, green, blue are uniformly distributed basis vectors
    # in 2 dimensions. the lowest value is
    if verbose[0]: print ("RGB-IN: {}".format (rgb));

    # scale the vector into canonical space ([0-1])
    rgb = vecMul (rgb, 1 / 255);

    # compute the linear combination of the basis vectors, and extract the saturation
    # XXX probably a pythonese way of doing this
    combination = vecAdd (vecAdd (vecMul (basis[0], rgb[0]), vecMul (basis[1], rgb[1])), vecMul (basis[2], rgb[2]));
    saturation = vecLen (combination);

    # if saturation is essentially 0, just go to the full on
    if (saturation <= epsilon):
        cw = 1;
        rgb = (0, 0, 0);
    else:
        # compute cw as the inverse of the saturation, and pre-compute the saturated color
        # in basis space
        cw = 1 - saturation;
        saturated = vecMul (combination, 1 / saturation);

        # we want to compute the actual RGB color of the saturated point as a linear
        # combination of no more than two of the basis vectors. first we have to figure
        # out which of the basis vectors we will use
        maxAngle = math.cos ((math.pi * 2 / 3) - epsilon);
        mask = tuple([(1 if (vecDot (saturated, vector) > maxAngle) else 0) for vector in basis]);
        count = sum(mask);
        if verbose[0]: print ("    Max Angle: {:0.3f}, Mask: ({}, {}, {}), Count: {}".format (maxAngle, mask[0], mask[1], mask[2], count));
        if (count == 1):
            # easy case, it's just one color component
            rgb = mask;
        else:
            # recast as a ray-line intersection using the two found basis vectors, note
            # the basis vectors are normalized by definition
            subBasis = [basis[i] for i, maskVal in enumerate(mask) if (maskVal == 1)];
            printBasis (subBasis, "    ");

            # define the line from the origin along the second vector, computing its
            # equation in the form Ax + C = 0, but C is always 0 for this line
            AB = (subBasis[1][1], subBasis[1][0] * -1);

            # intersect the ray from the saturation point along the first basis vector
            # with the line we just computed, these are definitely not co-linear, so there
            # should always be an intersection point, and the result should always be in
            # the range [-1 .. 1], this is the first basis coefficient
            coeff = [0, 0];
            coeff[0] = vecDot (saturated, AB) / vecDot (subBasis[0], AB);

            # compute the intersection point, and the second basis coefficient, note that
            # we compute b0 and b1 to always be positive, but the intersection calculation
            # needs to case in the opposite direction from the basis vector.
            intersection = vecAdd (vecMul (subBasis[0], -coeff[0]), saturated);
            coeff[1] = vecDot (intersection, subBasis[1]);

            if verbose[0]: print ("    Intersection: {}, b: {}".format (vecFormat (intersection), vecFormat (coeff)));

            # now rebuild the vector
            j = 0;
            rgbList = [];
            for i in range (len (rgb)):
                if (mask[i] == 1):
                    rgbList.append (min (coeff[j], 1));
                    j += 1;
                else:
                    rgbList.append (0);
            rgb = tuple (rgbList);

    # we want a discontinuous behavior, if cw < 0.5, we want the color to remain saturated
    # above 0.5, we want to desaturate the color
    # note: the Philips app caps cw at 140 and uses just the warm white, but I can't see a
    # difference in the bulb from 128 and up. we combine the cold_white and warm_white for
    # a truer color representation.
    cwMax = 128;
    if (cw > 0.5):
        rgb = vecMul (rgb, 1 - ((cw - 0.5) * 2));
    cw = min (1 + int (cw * 2 * cwMax), cwMax);

    # scale back to 1-255
    rgb = vecInt (vecMul (rgb, 255));

    # scale cw back to 1-255 and return the Pilot Builder that includes the white light
    if verbose[0]: print ("    RGB-OUT: {}, CW: {}".format (rgb, cw));

    # the wiz light appears to have 5 different LEDs, r, g, b, warm_white, and cold_white
    # there appears to be a max power supplied across the 5 LEDs, which explains why all-
    # on full isn't the brightest configuration
    # warm_white appears to be 2800k, and cold_white appears to be 6200k, somewhat neutral
    # brightness is achieved by turning both of them on
    return PilotBuilder(rgb = rgb, warm_white = cw, cold_white = cw);

def rgbcw2rgb (rgb, cw):
    print ("Hi");
