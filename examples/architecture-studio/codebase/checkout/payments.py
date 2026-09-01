"""Payment adapter."""


def authorize(cart):
    return {"status": "authorized", "total": len(cart)}
