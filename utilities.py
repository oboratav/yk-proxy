import base64

def extract_credentials(encoded_string: str) -> tuple:
    """
    Given the base64-encoded part of the authentication header, 
    decodes and separates the username and password.
    """
    decoded = base64.b64decode(encoded_string).decode("utf-8").split(":")
    return (decoded[0], decoded[1])

def parameter_as_list(parameter) -> list:
    """
    If a query parameter is repeated, falcon returns it as a list.
    If it isn't repeated, falcon returns it as a string. This function
    simplifies this behaviour by converting everything into a list.
    """
    if type(parameter) == list:
        return parameter
    elif type(parameter) == str:
        return [parameter]