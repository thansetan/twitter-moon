class TimeoutError(Exception):
    def __init__(self, duration: float):
        self.duration = duration
