from decimal import Decimal
from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib import messages

from payment.models import Order, OrderItem
from .cart import Cart
from store.models import Product
import json
from django.conf import settings
from store.models import Product
from decimal import Decimal

from django.conf import settings


class Cart:
    def __init__(self, request):
        """
        Initialize the cart.
        """
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart

    def add(self, product, quantity=1, update_quantity=False):
        """
            Add a product to the cart or update its quantity.
        """
        product_id = str(product.id)
        if product_id not in self.cart:
            self.cart[product_id] = {'quantity': 0, 'price': str(product.price)}
        if update_quantity:
            self.cart[product_id]['quantity'] = quantity
        else:
            self.cart[product_id]['quantity'] += quantity
        self.save()

    def update(self, product, quantity):
        """
        Update the quantity of a product in the cart.
        """
        product_id = str(product.id)
        if product_id in self.cart:
            self.cart[product_id]['quantity'] = quantity
            self.save()

    def save(self):
        """
        Mark the session as "modified" to make sure it gets saved.
        """
        self.session.modified = True

    def remove(self, product):
        """
        Remove a product from the cart.
        """
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def __iter__(self):
        """
        Iterate over the items in the cart and get the products from the database.
        """
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids)
        cart = self.cart.copy()
        for product in products:
            cart[str(product.id)]['product'] = product

        for item in cart.values():
            item['price'] = float(item['price'])
            item['total_price'] = item['price'] * item['quantity']
            yield item

    def __len__(self):
        """
        Count all items in the cart.
        """
        return sum(item['quantity'] for item in self.cart.values())

    def get_total_price(self):
        """
        Calculate the total cost of the items in the cart.
        """
        return sum(float(item['price']) * item['quantity'] for item in self.cart.values())

    def clear(self):
        """
        Remove cart from session.
        """
        del self.session[settings.CART_SESSION_ID]
        self.save()

    def get_products(self):
        """
        Get all the products in the cart.
        """
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids)
        return products

    def get_quantities(self):
        """
        Get quantities of all products in the cart.
        """
        quantities = {int(product_id): item['quantity'] for product_id, item in self.cart.items()}
        return quantities

    def get_subtotal(self):
        """
        Calculate the subtotal cost of the items in the cart.
        """
        products = self.get_products()
        quantities = self.get_quantities()
        subtotal = sum(product.price * quantities[product.id] for product in products)
        return subtotal
    
    def get_total_price(self):
        """
        Calculate the total price of the items in the cart.
        """
        return sum(float(item['price']) * item['quantity'] for item in self.cart.values())


def cart_summary(request):
    cart = Cart(request)
    cart_products = cart.get_products()
    quantities = cart.get_quantities()
    
    # Convert quantities keys to strings if they are not already
    quantities = {str(key): value for key, value in quantities.items()}
    
    # Debugging: Print quantities and product IDs
    print("Quantities:", quantities)
    print("Product IDs:", [product.id for product in cart_products])
    
    # Calculate the subtotal
    try:
        subtotal = sum(product.price * quantities[str(product.id)] for product in cart_products)
    except Exception as e:
        print("Error calculating subtotal:", e)
        subtotal = 0
    
    empty_message = "Your cart is currently empty." if not cart_products else None
    
    return render(request, "cart_summary.html", {
        "cart_products": cart_products,
        "quantities": quantities,
        "subtotal": subtotal,
        "empty_message": empty_message
    })
    
def cart_add(request):
    cart = Cart(request)
    if request.method == "POST":
        product_id = int(request.POST.get('product_id'))
        product_qty = int(request.POST.get('product_qty'))

        product = get_object_or_404(Product, id=product_id)
        cart.add(product=product, quantity=product_qty)

        cart_quantity = len(cart)
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

def cart_update(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    quantity = int(request.POST.get('quantity', 1))
    cart.update(product, quantity)
    return redirect('cart_summary')

# def cart_update(request):
#     cart = Cart(request)
#     if request.method == 'POST':
#         product_id = int(request.POST.get('product_id'))
#         product_qty = int(request.POST.get('product_qty'))
#         product = get_object_or_404(Product, id=product_id)

#         cart.update(product=product, quantity=product_qty)

#         response = JsonResponse({'qty': product_qty})
#         return response
    
def cart_view(request):
    cart_products = Cart.objects.all()  # Adjust as needed to get the user's cart
    quantities = {item.product.id: item.quantity for item in cart_products}
    
    subtotal = sum(item.product.price * item.quantity for item in cart_products)
    
    context = {
        'cart_products': cart_products,
        'quantities': quantities,
        'subtotal': subtotal,
    }
    return render(request, 'cart.html', context)

def checkout_view(request):
    cart = Cart(request)
    subtotal = cart.get_subtotal()
    shipping = Decimal('10.00')  # Example shipping cost, converted to Decimal
    tax = subtotal * Decimal('0.1')  # Example tax rate (10%), converted to Decimal
    total = subtotal + shipping + tax

    context = {
        'subtotal': subtotal,
        'shipping': shipping,
        'tax': tax,
        'total': total,
    }
    return render(request, 'checkout.html', context)

def place_order_view(request):
    cart = Cart(request)
    cart_products = cart.get_products()
    if not cart_products.exists():
        messages.error(request, "Your cart is empty!")
        return redirect('cart')

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
