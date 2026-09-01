"""HTTP-facing checkout entrypoint."""

from checkout.orders import place_order


def handle_checkout(cart):
    return place_order(cart)
