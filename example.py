#!/usr/local/opt/python@3.9/bin/python3.9

import asyncio;
import time;
import math;
import operator;

from pywizlight.bulb import PilotBuilder, PilotParser, wizlight
from  pywizlight import discovery

light = wizlight("192.168.1.217")

# a small value, really close to zero, more than adequate for our 3 orders of magnitude
# of color resolution
epsilon = 1.0e-5;

def vecDot (a, b):
    return sum(map(operator.mul, a, b));

def vecLenSq (a):
    return vecDot (a, a);

def vecLen (a):
    lenSq = vecLenSq (a);
    return math.sqrt (lenSq) if (lenSq > epsilon) else 0;

def vecAdd (a, b):
    return tuple(map (operator.add, a, b));

def vecSub (a, b):
    return tuple(map (operator.sub, a, b));

def vecMul (vec, sca):
    return tuple([c * sca for c in vec]);

def vecInt (vec):
    return tuple([int (c) for c in vec]);

def vecNormalize (vec):
    len = vecLen (vec);
    return vecMul (vec, 1 / len) if (len > epsilon) else vec;

def vecFormat (vec):
    return "({})".format (str([float ("{0:.3f}".format(n)) for n in vec])[1:-1]);

# red, green, blue basis vectors to simulate the homekit color wheel - just vectors at 3
# angles (0, 120, 240)
angle = (math.pi * 2) / 3;
basis = (
    (math.cos (0), math.sin (0)),
    (math.cos (angle), math.sin (angle)),
    (math.cos (angle * 2), math.sin (angle * 2))
);

def printBasis (basis, prefix = ""):
    print ("{}Basis Vectors: ".format (prefix), end = "");
    for vector in basis:
        print ("{} ".format (vecFormat (vector)), end="");
    print ("");
printBasis (basis);

def linearCombination (rgb):
    # XXX probably a pythonese way of doing this
    # sum the basis vectors
    return vecAdd (vecAdd (vecMul (basis[0], rgb[0]), vecMul (basis[1], rgb[1])), vecMul (basis[2], rgb[2]));

# compute the distance from the origin for a linear combination of the rgb basis vectors
def saturation (rgb):
    position = linearCombination (rgb);
    saturation = vecLen (position);
    print ("RGB: {}, Distance: {:0.3f}".format (rgb, saturation));
    return saturation;

def replaceAtIndex(tup, ix, val):
    return tup[:ix] + (val,) + tup[ix+1:]

def rgb2rgbcw (rgb):
    # in the homekit color wheel, red, green, blue are uniformly distributed basis vectors
    # in 2 dimensions. the lowest value is
    print ("RGB-IN: {}".format (rgb));

    # scale the vector into canonical space ([0-1])
    rgb = vecMul (rgb, 1 / 255);

    # compute the linear combination of the basis vectors, and extract the saturation
    combination = linearCombination (rgb);
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
        print ("    Max Angle: {:0.3f}, Mask: ({}, {}, {}), Count: {}".format (maxAngle, mask[0], mask[1], mask[2], count));
        if (count == 1):
            # easy case, it's just one color component
            rgb = mask;
        else:
            # recast as a ray-line intersection using the two found basis vectors, note
            # the basis vectors are normalized by definition

            print ("    Saturated: {}".format (vecFormat (saturated)));

            projected = tuple (map (lambda vector: abs(vecDot (saturated, vector)), basis));
            print ("    Projected: {}".format (vecFormat (projected)));

            print ("    Mask:      {}".format (vecFormat (mask)));

            rgb = tuple (map (lambda m, p: p if (m == 1) else 0, mask, projected));
            print ("    Masked:    {}".format (vecFormat (rgb)));

            # not using this ATM
            #if False:

            subBasis = [basis[i] for i, maskVal in enumerate(mask) if (maskVal == 1)];
            printBasis (subBasis, "    ");

            # define the line from the origin along the second vector, computing its
            # equation in the form Ax + C = 0, but C is always 0 for this line
            AB = (subBasis[1][1], subBasis[1][0] * -1);
            C = 0;

            # intersect the ray from the saturation point along the first basis vector
            # with the line we just computed, these are definitely not co-linear, so there
            # should always be an intersection point, and the result should always be in
            # the range [-1 .. 1], this is the first basis coefficient
            b0 = (vecDot (saturated, AB) + C) / (vecDot (subBasis[0], AB) * -1);

            # compute the intersection point, and the second basis coefficient, note that
            # b0 will always be negative, and b1 will always be positive, so we fix b0
            intersection = vecAdd (vecMul (subBasis[0], b0), saturated);
            b1 = vecDot (intersection, subBasis[1]);
            b0 = -b0;

            print ("    Intersection: {}, b0: {:0.3f}, b1: {:0.3f}".format (vecFormat (intersection), b0, b1));

            # now rebuild the vector
            # XXX todo

    # the lowest value was a modifier on the other two vectors, and can be replaced by
    # reducing the coefficients of the other two basis vectors. conveniently, the amount
    # happens to be value itself. the lowest value is also the cw value we want.

    # we want a discontinuous behavior, if cw < 0.5, we want the color to remain saturated
    # above 0.5, we want to desaturate the color
    if (cw > 0.5):
        rgb = vecMul (rgb, 1 - ((cw - 0.5) * 2));
    rgb = vecInt (vecMul (rgb, 255));

    # scale cw back to 1-255 and return the Pilot Builder that includes the white light
    # the Philips app caps it at 140
    cwMax = 140;
    cw = min (1 + int (cw * 254), cwMax);
    print ("    RGB-OUT: {}, CW: {}".format (rgb, cw));
    return PilotBuilder(rgb = rgb, warm_white = cw, cold_white = cw);

async def main():

    await light.turn_off();

    for step in range (26):
        stepVal = 5 + (step * 10);
        await light.turn_on(rgb2rgbcw ((255,stepVal,255)));

    time.sleep (5);
    await light.turn_off();

loop = asyncio.get_event_loop();
loop.run_until_complete(main());


