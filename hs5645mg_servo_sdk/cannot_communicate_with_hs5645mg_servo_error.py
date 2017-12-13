class CannotCommunicateWithHS5485HBError(Exception):
    def __init__(self):
        pass

    def __str__(self):
        return "Couldn't communicate with HS5485HB servo motor."
