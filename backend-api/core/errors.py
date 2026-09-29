"""One error type for broken business rules.

Core functions raise RuleError("message the user can read"). app.py turns it into an HTTP
response {"detail": message}, so the core code never has to know about HTTP.
"""


class RuleError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class NotFound(RuleError):
    def __init__(self, message: str = "We couldn't find that."):
        super().__init__(message, 404)
