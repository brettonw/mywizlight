#!/usr/bin/env python3

import asyncio;
import time;

from pywizlight.bulb import PilotBuilder, PilotParser, wizlight;

from mylights import getLightIp;

light = wizlight (getLightIp ());

async def main():
    lastState = await light.updateState();
    print("Scene: {}, JSON: {}".format(lastState.get_scene(), lastState.__dict__["pilotResult"]));

    while 1 < 6:
        state = await light.updateState();

        # see if the new state matches the last state
        coldWhiteMatches = (state.get_cold_white() == lastState.get_cold_white());
        warmWhiteMatches = (state.get_warm_white() == lastState.get_warm_white());
        rgbMatches = (state.get_rgb() == lastState.get_rgb());
        if (not (coldWhiteMatches and warmWhiteMatches and rgbMatches)):
            print("Scene: {}, JSON: {}".format(state.get_scene(), state.__dict__["pilotResult"]));
            lastState = state;

loop = asyncio.get_event_loop();
loop.run_until_complete(main());
