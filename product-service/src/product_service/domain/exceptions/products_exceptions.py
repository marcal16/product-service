class DataNotProvided(Exception):
    """Raised when the required data is not provided."""
    pass

class ProductNotFound(Exception):
    """Raised when a product is not found in the database."""
    pass

class ProductAlreadyExists(Exception):
    """Raised when trying to create a product that already exists."""
    pass

class InvalidProductData(Exception):
    """Raised when the provided product data is invalid."""
    pass 

class InsufficientQuantity(Exception):
    """Raised when there is insufficient quantity of a product."""
    pass