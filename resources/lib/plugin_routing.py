import routing
import sys
import logging

logging.debug('Addon Args: %s' % sys.argv)

plugin = routing.Plugin()


def arg_as_bool(arg):
    if arg in plugin.args:
        val = plugin.args[arg][0]
        if val:
            return True
    return False


def arg_as_string(arg):
    return plugin.args[arg][0] if arg in plugin.args else ''

def arg_as_number(arg):
    val = arg_as_string(arg)
    try:
        return int(float(val))
    except:
        return None
