import sys;

MYLIGHTS = {
    "office": "192.168.1.217",
    "nook": "192.168.1.230"
};

def getLightIp ():
    if (len (sys.argv) > 1):
        # read the second argument
        light = sys.argv[1];
        if light in MYLIGHTS:
            print ("Using {} ({})".format (light, MYLIGHTS[light]));
            return MYLIGHTS[light];
        if light.startswith ("192.168"):
            # could do more to validate this, like reverse index MYLIGHTS...
            print ("Using supplied IP ({})".format (light));
            return light;
        print ("Unknown light".format (light));
    # default to the office light
    print ("Default to office light ({})".format (MYLIGHTS["office"]));
    return MYLIGHTS["office"];
