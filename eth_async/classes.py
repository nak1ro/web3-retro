class AutoRepr:
    """Automatically generates a __repr__ string for any class based on its attributes."""

    def __repr__(self) -> str:
        values = (f'{key}={value!r}' for key, value in vars(self).items())
        return f'{self.__class__.__name__}({", ".join(values)})'


class Singleton:
    """Implements the singleton pattern, ensuring a class only has one instance."""
    _instances = {}

    def __new__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__new__(cls)
        return cls._instances[cls]
