import logging


def loglevel(name):
    return logging._nameToLevel[name.upper()]


def max_str(s, max_len=100):
    if len(s) > max_len:
        s = s[0:max_len] + " ..."
    return s
