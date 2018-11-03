

def generate_xorg_conf(bus_ids, mode, options=[]):

    if mode == "nvidia":
        return _generate_nvidia(bus_ids, options)
    elif mode == "intel":
        return _generate_intel(bus_ids, options)


def _generate_nvidia(bus_ids, options):

    text = \
"""
Section \"Module\"
\tLoad \"modesetting\"
EndSection

Section \"Device\"
\tIdentifier \"nvidia\"
\tDriver \"nvidia\"
"""

    text += "\tBusID \"%s\"\n" % bus_ids["nvidia"]
    text += "\tOption \"AllowEmptyInitialConfiguration\"\n"

    if "overclocking" in options:
        text += "\tOption \"Coolbits\" \"28\"\n"

    if "triple_buffer" in options:
        text += "\"TripleBuffer\" \"true\"\n"

    text += "EndSection\n"

    return text


def _generate_intel(bus_ids, options):

    text = \
"""
Section \"Device\"
\tIdentifier  \"intel\"
\tDriver      \"modesetting\"
"""

    text += "\tBusID \"%s\"\n" % bus_ids["intel"]

    if "dri_3" in options:
        text += "\tOption \"DRI\" \"3\"\n"

    text += "EndSection\n"

    return text
