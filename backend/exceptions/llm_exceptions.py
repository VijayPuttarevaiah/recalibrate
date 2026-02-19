class LLMClientError(Exception):
    def __init__(
        self,
        message: str,
        *,
        status_code: int = 503,
        error_code: str = "llm_unavailable",
        retryable: bool = True,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.retryable = retryable

    def to_http_detail(self) -> dict:
        return {
            "error_code": self.error_code,
            "message": self.message,
            "retryable": self.retryable,
        }
