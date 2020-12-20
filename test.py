#!/usr/bin/env python3

import asyncio;
import time;
import sys;

from mylights import getLight;

from rgb2rgbcw import rgb2rgbcw, setVerbose;
setVerbose (True);

numSteps = 32;
stepSize = int (256 / numSteps);

async def myColor (light, step):
    stepVal = min (step * stepSize, 255);
    await light.turn_on(rgb2rgbcw ((255, stepVal, 255)));

async def main():
    light = getLight ();
    if not light is None:
        resp = await light.getBulbConfig()
        if resp is not None and "result" in resp:
            for key, value in resp["result"].items() :
                print (key, value)
        else:
            print ("CONFIG: NO RESPONSE");
        #if "moduleName" in bulb_config["result"]:
        #        self._bulbtype = bulb_config["result"]["moduleName"]

        await myColor (light, 0);
        time.sleep (5);

        for step in range (numSteps + 1):
            await myColor (light, step);

        time.sleep (5);

loop = asyncio.get_event_loop();
loop.run_until_complete(main());


