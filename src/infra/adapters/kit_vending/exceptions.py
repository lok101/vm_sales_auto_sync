class ResolverCacheLoadingError(Exception):
    pass


class SalesProviderAdapterException(Exception):
    pass


class SaleProviderMappingException(SalesProviderAdapterException):
    pass


class SaleProviderResolutionException(SalesProviderAdapterException):
    pass
