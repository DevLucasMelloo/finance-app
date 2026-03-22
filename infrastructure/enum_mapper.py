from enum import Enum


def enum_from_db(enum_cls: type[Enum], value: str) -> Enum:
    """
    Safely converts a database string value into an Enum.
    Raises a clear error if the value is invalid.
    """
    try:
        return enum_cls(value)
    except ValueError:
        valid = [e.value for e in enum_cls]
        raise ValueError(
            f"Valor '{value}' inválido para {enum_cls.__name__}. "
            f"Valores válidos: {valid}"
        )
