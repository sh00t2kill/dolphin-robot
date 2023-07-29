class LoginError(Exception):
    def __init__(self):
        self.error = "Failed to login"
