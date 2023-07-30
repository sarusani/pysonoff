def parseAddress(address):
    """
    Resolve the IP address of the device
    :param address:
    :return: add_str
    """
    add_list = []
    for i in range(4):
        add_list.append(int(address.hex()[(i * 2): (i + 1) * 2], 16))
    add_str = (
        str(add_list[0])
        + "."
        + str(add_list[1])
        + "."
        + str(add_list[2])
        + "."
        + str(add_list[3])
    )
    return add_str


def calculate_retry(retry_count):

    # increasing backoff each retry attempt
    wait_seconds = [2, 5, 10, 30, 60]

    if retry_count >= len(wait_seconds):
        retry_count = len(wait_seconds) - 1

    return wait_seconds[retry_count]
