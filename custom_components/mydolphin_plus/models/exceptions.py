class LoginError(Exception):
    def __init__(self, message: str = "Failed to login"):
        super().__init__(message)
        self.error = message
