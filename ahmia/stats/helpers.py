def round_to_next_multiple_of(number, divisor):
    """
    Return the lowest x such that x is at least the number
    and x modulo divisor == 0
    """
    number = number + divisor - 1
    number = number - number % divisor
    return number
