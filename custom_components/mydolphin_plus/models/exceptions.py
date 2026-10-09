class LoginError(Exception):
    def __init__(self, message: str = "Failed to login"):
        super().__init__(message)
        self.error = message


class CognitoAuthError(LoginError):
    """Cognito explicitly rejected the authentication credentials."""


class CognitoRequestError(LoginError):
    """A non-authentication error occurred while calling Cognito."""
