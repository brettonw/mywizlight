#!/usr/bin/env python3

import sys
import asyncio

from mylights import getLight

try: from .rgb2rgbcw import rgb2rgbcw, setVerbose, discretize;
except: from rgb2rgbcw import rgb2rgbcw, setVerbose, discretize;

setVerbose (True)

divisions = 5
width = 1
tests = 8
for x in range(tests + 1):
    y = ((x + 0.75) / tests) * width
    z = discretize (y, divisions, width)
    passTest = ((z - y) <= ((width / (divisions - 1)) / 2))
    print ("X: {}, Y: {:0.3f}, Z: {}, PASS: {}".format (x, y, z, "PASS" if (passTest) else "FAIL"))

# get the color as three inputs
rgb = tuple([int (c) for c in sys.argv[2].split(",")])

async def main():
    light = getLight ()
    if not light is None:
        await light.turn_on(rgb2rgbcw (rgb, None))

loop = asyncio.get_event_loop()
loop.run_until_complete(main())


