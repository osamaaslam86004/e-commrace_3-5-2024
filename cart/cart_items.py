import json
from decimal import Decimal  # Import Decimal module
from django.db.models.fields.files import ImageFieldFile  # Import ImageFieldFile

MAX_HISTORY_ITEMS = 7  # Maximum number of items to store in the browsing history
MAX_COOKIE_SIZE = 4000  # Maximum size of the cookie data in bytes (4KB)


def add_product_to_cart_history(request, cart_items_in_cookie):
    # Fetch existing browsing history from the session or initialize an empty dictionary
    items_in_cart = request.session.get("cart_items", [])

    # Add details of the new product to the browsing history lists
    items_in_cart.append(cart_items_in_cookie)

    # Ensure all lists in browsing history don't exceed the maximum length
    items_in_cart = items_in_cart[-MAX_HISTORY_ITEMS:]

    # Serialize the browsing history to JSON to estimate its size
    cart_json = json.dumps(items_in_cart)

    cookie_size = len(cart_json.encode("utf-8"))

    # Check if the cookie size exceeds the limit
    if cookie_size > MAX_COOKIE_SIZE:
        # Calculate the excess size and trim lists to fit within the size limit
        excess = cookie_size - MAX_COOKIE_SIZE
        excess_history = json.loads(cart_json[:excess].decode("utf-8"))
        items_in_cart = items_in_cart[len(excess_history) :]

    # Update the session with the modified browsing history
    request.session["cart_items"] = items_in_cart
    request.session.modified = True


def your_cart_items(request):
    if "cart_items" in request.session:
        items_in_cart = request.session.get("cart_items")
        return items_in_cart
    else:
        return []
