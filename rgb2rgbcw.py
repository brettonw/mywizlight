#!/usr/bin/env python3

import math
import operator

from pywizlight.bulb import PilotBuilder, PilotParser, wizlight

try: from .vec import *;
except: from vec import *;

# can't actually change a value like this from another files once it's been loaded. this
# is actually a very bad design on python's part IMNSHO, and this is an ugly workaround
verbose = [False]
def setVerbose (val):
    verbose[0] = val

def debug (msg, end = "\n"):
    if (verbose[0]): print (msg, end = end);

# red, green, blue basis vectors from the hue/saturation color wheel - just vectors at 3
# angles (0, 120, 240)
angle = (math.pi * 2) / 3
basis = (
    vecFromAngle (0),
    vecFromAngle (angle),
    vecFromAngle (angle * 2)
)

def printBasis (basis, prefix = ""):
    debug ("{}Basis Vectors: ".format (prefix), end = "")
    for vector in basis:
        debug ("{} ".format (vecFormat (vector)), end="")
    debug ("")

# this function computes the linear combination of two basis vectors that define a trapezoid
# hueVec - a normalized vector in the hue color wheel (0..1, 0..1, 0..1)
# saturation - a single value representing the length of the hue vector (0..1)
# brightness - a separate value that may be passed in, and should be used in the Pilot
def trapezoid (hueVec, saturation, brightness):
    # if saturation is essentially 0, just go to the full on
    if (saturation <= epsilon):
        rgb = (0, 0, 0)
    else:
        # we want to compute the actual RGB color of the saturated point as a linear
        # combination of no more than two of the basis vectors. first we have to figure
        # out which of the basis vectors we will use
        maxAngle = math.cos ((math.pi * 2 / 3) - epsilon)
        mask = tuple([(1 if (vecDot (hueVec, vector) > maxAngle) else 0) for vector in basis])
        count = sum(mask)
        debug ("    Max Angle: {:0.3f}, Mask: ({}, {}, {}), Count: {}".format (maxAngle, mask[0], mask[1], mask[2], count))
        if (count == 1):
            # easy case, it's just one color component
            rgb = mask
        else:
            # recast as a ray-line intersection using the two found basis vectors, note
            # the basis vectors are normalized by definition
            subBasis = [basis[i] for i, maskVal in enumerate(mask) if (maskVal == 1)]
            printBasis (subBasis, "    ")

            # define the line from the origin along the second vector, computing its
            # equation in the form Ax + C = 0, but C is always 0 for this line
            AB = (subBasis[1][1], subBasis[1][0] * -1)

            # intersect the ray from the saturation point along the first basis vector
            # with the line we just computed, these are definitely not co-linear, so there
            # should always be an intersection point, and the result should always be in
            # the range [-1 .. 1], this is the first basis coefficient
            coeff = [0, 0]
            coeff[0] = vecDot (hueVec, AB) / vecDot (subBasis[0], AB)

            # compute the intersection point, and the second basis coefficient, note that
            # we compute the coefficients to always be positive, but the intersection calculation
            # needs to be in the opposite direction from the basis vector (hence the negative on
            # coeff[0]).
            intersection = vecAdd (vecMul (subBasis[0], -coeff[0]), hueVec)
            coeff[1] = vecDot (intersection, subBasis[1])

            debug ("    Intersection Point: {}, Coefficients: {}".format (vecFormat (intersection), vecFormat (coeff)))

            # there's a bit of a gamut problem here, as the area outside the hexagon defined by
            # the three unit basis vectors is not actually reachable. this manifests as
            # coefficients greater than 1, which will always happen unless the target color is
            # either one of the basis vectors or a bisector of two basis vectors. we scale both
            # coefficients by 1/maxCoefficient to make valid colors
            maxCoeff = max (coeff[0], coeff[1])
            coeff = [c / maxCoeff for c in coeff]
            debug ("    Scaled Coefficients: {}".format (vecFormat (coeff)))

            # now rebuild the rgb vector by putting the coefficients into the correct place
            j = 0
            rgbList = []
            for i in range (3):
                if (mask[i] == 1):
                    rgbList.append (min (coeff[j], 1))
                    j += 1
                else:
                    rgbList.append (0)
            rgb = tuple (rgbList)

    # we want a discontinuous behavior. if saturation >= 0.5, we want the color to remain saturated
    # and we scale the cw value down to 0 as saturation goes from 0.5 to 1. if saturation < 0.5, we
    # want to saturate cw, and scale the rgb down to (0, 0, 0) as saturation goes from 0.5 - 0
    if (saturation >= 0.5):
        # rgb remains saturated
        # scale the cw value down to 0 as saturation goes from 0.5 to 1
        cw = 1 - ((saturation - 0.5) * 2)
    else:
        cw = 1
        rgb = vecMul (rgb, saturation * 2)

    # scale back to the pilot color space
    rgb = vecInt (vecMul (rgb, 255))
    cw = int (max (0, cw * cwMax))
    if (cw == 0): cw = None;

    # scale cw back to 1-255 and return the Pilot Builder that includes the white light
    debug ("    RGB-OUT: {}, CW: {}".format (rgb, cw))

    # the wiz light appears to have 5 different LEDs, r, g, b, warm_white, and cold_white
    # there appears to be a max power supplied across the 5 LEDs, which explains why all-
    # on full isn't the brightest configuration
    # warm_white appears to be 2800k, and cold_white appears to be 6200k, somewhat neutral
    # brightness is achieved by turning both of them on
    return PilotBuilder(rgb = rgb, warm_white = cw, cold_white = cw, brightness = brightness)

# the max value we will use for c and w
cwMax = 128

def rgb2rgbcw (rgb, brightness):
    debug ("RGB-IN: {}, BRIGHTNESS: {}".format (rgb, brightness))

    # scale the vector into canonical space ([0-1])
    rgb = vecMul (rgb, 1 / 255)

    # compute the linear combination of the basis vectors, and extract the saturation
    # XXX probably a pythonese way of doing this
    hueVec = vecAdd (vecAdd (vecMul (basis[0], rgb[0]), vecMul (basis[1], rgb[1])), vecMul (basis[2], rgb[2]))
    saturation = vecLen (hueVec)
    if (saturation > epsilon):
        hueVec = vecMul (hueVec, 1 / saturation)

    return trapezoid(hueVec, saturation, brightness)

# given a tuple that is r,g,b and cw in 0-255 range, convert that to an r,g,b tuple
def rgbcw2rgb (rgb, cw):
    rgb = vecMul (rgb, 1 / 255)
    cw /= cwMax
    if (cw == 1):
        # cw is fully saturated, and rgb scales down to white
        debug ("High")
    else:
        # the rgb vector is fully saturated, and cw scales from 0-0.5 to add in white light
        debug ("Low")

# x = canonicalValue
# n = number of divisions
# w = scale
def discretize (x, n, w):
    s = 1 / (n - 1)
    y = int ((x + (s / 2)) / s)
    z = y * s
    return z * w

def hs2rgbcw (hs, brightness):
    # convert hue to a canonical value
    hueCanonical = hs[0] / 360
    while (hueCanonical >= 1): hueCanonical -= 1;

    # compute hue in a discretized space and convert to radians, then a vector
    hueRadians = discretize (hueCanonical, 3 * 8, math.pi * 2)
    hueVec = vecFromAngle(hueRadians)

    # convert saturation to a canonical value in a discretized space
    # we take the square root to give the user more visual control
    saturationCanonical = hs[1] / 100
    saturation = discretize (math.sqrt(saturationCanonical), 8, 1)

    debug ("HS: {}, HUE: {:.5f}, SATURATION: {:.3f}, BRIGHTNESS: {}".format (vecFormat(hs), hueRadians, saturation, brightness))

    return trapezoid (hueVec, saturation, brightness)
