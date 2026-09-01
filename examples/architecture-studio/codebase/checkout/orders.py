"""Order orchestration."""

from checkout.payments import authorize
from checkout.persistence import save_order


def place_order(cart):
    authorization = authorize(cart)
    return save_order(cart, authorization)
