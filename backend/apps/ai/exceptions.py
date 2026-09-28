class AIProviderError(Exception):
    def __init__(self, code, detail):
        self.code = code
        self.detail = detail
        super().__init__(detail)

class AIProviderTimeout(AIProviderError):
    pass

class AIProviderInvalidCredentials(AIProviderError):
    pass

class AIProviderRateLimited(AIProviderError):
    pass
