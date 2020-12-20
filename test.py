#!/usr/bin/env python3

import asyncio;
import time;

from pywizlight.bulb import PilotBuilder, PilotParser, wizlight

from mylights import getLightIp;
from rgb2rgbcw import rgb2rgbcw, setVerbose;
setVerbose (True);

light = wizlight (getLightIp ());

numSteps = 32;
stepSize = int (256 / numSteps);

async def myColor (step):
    stepVal = min (step * stepSize, 255);
    await light.turn_on(rgb2rgbcw ((255, stepVal, 255)));

async def main():

    await myColor (0);
    time.sleep (5);

    for step in range (numSteps + 1):
        await myColor (step);

    time.sleep (5);

loop = asyncio.get_event_loop();
loop.run_until_complete(main());


