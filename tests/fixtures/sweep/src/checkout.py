from src.orders import create_order
from src.shipping import shipping_cost


def checkout(cart):
    return create_order(cart), shipping_cost(cart)
