"""Persistence adapter."""


def save_order(cart, authorization):
    return {"items": cart, "authorization": authorization}
