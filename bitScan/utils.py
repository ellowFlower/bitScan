def create_sub_version():
    """Binary encode the sub-version

    Returns: Binary encodes sub-version as bytes
    """
    sub_version = "/Satoshi:0.7.2/"
    return b'\x0F' + sub_version.encode()