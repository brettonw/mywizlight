#!/usr/bin/env python3

import asyncio;
import time;

from mylights import getLight;

def printMap (m, title = "Map", keys = None):
    print ("{} = (".format (title), end = "");
    separator = "";
    if (keys is None):
        for key, value in m.items() :
            print ("{}{}: {}".format (separator, key, value), end = "");
            separator = ", ";
    else:
        for key in keys:
            if key in m:
                print ("{}{}: {}".format (separator, key, m[key]), end = "");
                separator = ", ";
    print (")");

def checkDifferent (a, b, keys):
    for key in keys:
        keyCount = (1 if (key in a) else 0) + (1 if (key in b) else 0);
        if ((keyCount == 1) or ((keyCount == 2) and (a[key] != b[key]))):
            return True;
    return False;

async def main():
    light = getLight ();
    if not light is None:
        resp = await light.getBulbConfig()
        if resp is not None and "result" in resp:
            printMap (resp["result"], "Config", ["mac", "moduleName", "fwVersion", "ewf"]);

    lastState = await light.updateState();
    lastState = lastState.pilotResult;
    stateVals = ["temp", "r", "g", "b", "c", "w", "dimming"];
    printMap (lastState, "Start ", stateVals);

    while True:
        state = await light.updateState();
        state = state.pilotResult;

        # see if the new state matches the last state
        if checkDifferent (lastState, state, stateVals):
            printMap (state, "Update", stateVals);
            lastState = state;


loop = asyncio.get_event_loop();
loop.run_until_complete(main());
