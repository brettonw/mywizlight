import sys;
from pywizlight.bulb import PilotBuilder, PilotParser, wizlight

lightIpsByName = {
    "office": "192.168.1.217",
    "nook":   "192.168.1.230"
};
lightNamesByIp = {v: k for k, v in lightIpsByName.items()};

def makeLight (name):
    ip = lightIpsByName[name];
    print ("Light: {} ({})".format (name, ip));
    return wizlight (ip);

def getLight ():
    # default to the office light (for testing)
    if (len (sys.argv) > 1):
        # read the second argument
        light = sys.argv[1];
        if light in lightIpsByName:
            return makeLight (light);
        if light in lightNamesByIp:
            return makeLight (lightNamesByIp[light]);
        print ("Unknown light ({})".format (light));
    else:
        print ("ERROR: No light specified");
    return None;
