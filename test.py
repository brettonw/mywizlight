#!/usr/bin/env python3

import sys;
import asyncio;
import time;

from mylights import getLight;

from rgb2rgbcw import rgb2rgbcw, setVerbose;
setVerbose (True);

# get the color as three inputs
rgb = tuple([int (c) for c in sys.argv[2].split(",")]);

async def main():
    light = getLight ();
    if not light is None:
        await light.turn_on(rgb2rgbcw (rgb));

loop = asyncio.get_event_loop();
loop.run_until_complete(main());


