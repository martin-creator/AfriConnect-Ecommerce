from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib import messages
from .cart import Cart
from store.models import Product
import json


class Cart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get('cart')
        if not cart:
            cart = self.session['cart'] = {}
        self.cart = cart

    def add(self, product, quantity=1):
        product_id = str(product.id)
        if product_id not in self.cart:
            self.cart[product_id] = {'quantity': 0, 'price': str(product.price)}
        self.cart[product_id]['quantity'] += quantity
        self.save()

    def save(self):
        self.session.modified = True

    def remove(self, product):
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def update(self, product, quantity):
        product_id = str(product.id)
        if product_id in self.cart:
            self.cart[product_id]['quantity'] = quantity
            self.save()

    def get_products(self):
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids)
        return products

    def get_quantities(self):
        return {int(key): value['quantity'] for key, value in self.cart.items()}

    def cart_total(self):
        return sum(Decimal(item['price']) * item['quantity'] for item in self.cart.values())

    def __len__(self):
        return sum(item['quantity'] for item in self.cart.values())


def cart_summary(request):
    cart = Cart(request)
    cart_products = cart.get_products()
    quantities = cart.get_quantities()
    
    subtotal = sum(product.price * quantities[product.id] for product in cart_products)
    
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

def cart_update(request):
    cart = Cart(request)
    if request.method == 'POST':
        product_id = int(request.POST.get('product_id'))
        product_qty = int(request.POST.get('product_qty'))
        product = get_object_or_404(Product, id=product_id)

        cart.update(product=product, quantity=product_qty)

        response = JsonResponse({'qty': product_qty})
        return response
    
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
    cart_products = Cart.objects.all()  # Adjust as needed to get the user's cart
    subtotal = sum(item.product.price * item.quantity for item in cart_products)
    shipping = 10  # Example shipping cost
    tax = subtotal * 0.1  # Example tax rate (10%)
    total = subtotal + shipping + tax
    
    context = {
        'subtotal': subtotal,
        'shipping': shipping,
        'tax': tax,
        'total': total,
    }
    return render(request, 'checkout.html', context)

def place_order_view(request):
    cart_products = Cart.objects.all()  # Adjust as needed to get the user's cart
    if not cart_products:
        messages.error(request, "Your cart is empty!")
        return redirect('cart')

    # Calculate totals
    subtotal = sum(item.product.price * item.quantity for item in cart_products)
    shipping = 10  # Example shipping cost
    tax = subtotal * 0.1  # Example tax rate (10%)
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
    for item in cart_products:
        OrderItem.objects.create(
            order=order,
            product=item.product,
            quantity=item.quantity,
            price=item.product.price,
            total=item.product.price * item.quantity
        )

    # Clear the cart
    cart_products.delete()

    messages.success(request, "Your order has been placed successfully!")
    return redirect('order_confirmation', order_id=order.id)
