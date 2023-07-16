

def get_current_host(request):
    """
    Returns the current host URL based on the provided request object.

    Parameters:
        request (object): The request object containing information about the client's request.

    Returns:
        str: The current host URL constructed using the protocol and host extracted from the request.
    """
    protocol = request.is_secure() and "https://" or "http://"
    host = request.get_host()

    return "{protocol}{host}".format(protocol=protocol, host=host)
