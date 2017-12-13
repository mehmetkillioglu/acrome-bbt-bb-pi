class wiringpiNotFoundError(Exception):
    def __init__(self):
        pass

    def __str__(self):
        return "Please install wiringpi before using servo communicator."
