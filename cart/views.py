from decimal import Decimal
from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib import messages
from payment.models import Order, OrderItem, ShippingAddress
from payment.forms import ShippingForm
from .cart import Cart
from store.models import Product

# Cart Views
def cart_summary(request):
    cart = Cart(request)
    cart_products = cart.get_products()
    quantities = cart.get_quantities()
    subtotal = cart.get_subtotal()

    empty_message = "Your cart is currently empty." if not cart_products else None

    return render(request, "cart_summary.html", {
        "cart_products": cart_products,
        "quantities": quantities,
        "subtotal": subtotal,
        "empty_message": empty_message
    })

def cart_view(request):
    cart = Cart(request)
    cart_products = cart.get_products()
    quantities = cart.get_quantities()
    subtotal = cart.get_subtotal()
    shipping_cost = Decimal('10.00')  # Example shipping cost as Decimal
    total = subtotal + shipping_cost  # Add other costs like taxes if needed

    context = {
        'cart_products': cart_products,
        'quantities': quantities,
        'subtotal': subtotal,
        'shipping_cost': shipping_cost,
        'total': total,
    }
    return render(request, 'cart_summary.html', context)

def cart_add(request):
    cart = Cart(request)
    if request.method == "POST":
        product_id = int(request.POST.get('product_id'))
        product_qty = int(request.POST.get('product_qty'))

        product = get_object_or_404(Product, id=product_id)
        cart.add(product=product, quantity=product_qty)

        cart_quantity = sum(item['quantity'] for item in cart.cart.values())  # Calculate the total quantity in the cart
        response = JsonResponse({'qty': cart_quantity})
        return response


def cart_delete(request):
    cart = Cart(request)
    if request.method == 'POST':
        product_id = int(request.POST.get('product_id'))
        product = get_object_or_404(Product, id=product_id)
        cart.remove(product)

        response = JsonResponse({'product': product_id})
        return response





# Utility function to convert Decimals to floats or strings for JSON serialization
def decimal_to_float(value):
    if isinstance(value, Decimal):
        return float(value)
    raise TypeError

def cart_update(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    quantity = int(request.POST.get('quantity', 1))
    cart.update(product=product, quantity=quantity)

    # Recalculate subtotal and other necessary cart details
    cart_products = cart.get_products()
    subtotal = sum(product.price * cart.cart[str(product.id)]['quantity'] for product in cart_products)

    response_data = {
        'cart_products': [
            {
                'id': product.id,
                'name': product.name,
                'quantity': cart.cart[str(product.id)]['quantity'],
                'price': str(product.price),  # Convert Decimal to string
                'total': str(product.price * cart.cart[str(product.id)]['quantity'])  # Convert Decimal to string
            }
            for product in cart_products
        ],
        'subtotal': str(subtotal)  # Convert Decimal to string
    }

    return JsonResponse(response_data, safe=False, json_dumps_params={'default': decimal_to_float})


    
# Checkout Views
def checkout(request):
    cart = Cart(request)
    cart_products = cart.get_products()
    quantities = cart.get_quantities()
    subtotal = cart.get_subtotal()
    shipping_cost = Decimal('10.00')  # Ensure this is a Decimal
    total = subtotal + shipping_cost  # Add other costs like taxes if needed

    if request.user.is_authenticated:
        # Checkout as logged in user
        try:
            shipping_user = ShippingAddress.objects.get(user=request.user)
            shipping_form = ShippingForm(request.POST or None, instance=shipping_user)
        except ShippingAddress.DoesNotExist:
            shipping_form = ShippingForm(request.POST or None)
    else:
        # Checkout as guest
        shipping_form = ShippingForm(request.POST or None)

    return render(request, "checkout.html", {
        "cart_products": cart_products,
        "quantities": quantities,
        "subtotal": subtotal,
        "shipping_cost": shipping_cost,
        "total": total,
        "shipping_form": shipping_form
    })

def place_order_view(request):
    cart = Cart(request)
    cart_products = cart.get_products()
    if not cart_products.exists():
        messages.error(request, "Your cart is empty!")
        return redirect('cart_summary')

    # Calculate totals
    subtotal = sum(Decimal(item.price) * item.quantity for item in cart_products)
    shipping = Decimal('10.00')  # Example shipping cost as Decimal
    tax = subtotal * Decimal('0.1')  # Example tax rate (10%) as Decimal
    total = subtotal + shipping + tax

    # Create the order
    order = Order.objects.create(
        user=request.user,  # Assuming you have a user associated with the order
        subtotal=subtotal,
        shipping=shipping,
        tax=tax,
        total=total
    )

    # Create order items
    for product in cart_products:
        quantity = cart.cart[str(product.id)]['quantity']
        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=quantity,
            price=product.price,
            total=product.price * quantity
        )

    # Clear the cart
    cart.clear()

    messages.success(request, "Your order has been placed successfully!")
    return redirect('order_confirmation', order_id=order.id)
