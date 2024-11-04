from django.conf import settings
from store.models import Product, Profile
from decimal import Decimal

class Cart:
    def __init__(self, request):
        self.session = request.session
        self.request = request
        cart = self.session.get(settings.CART_SESSION_ID)

        if not cart:
            cart = self.session[settings.CART_SESSION_ID] = {}

        self.cart = cart

    def add(self, product, quantity):
        product_id = str(product.id)
        if product_id in self.cart:
            self.cart[product_id]['quantity'] += quantity
        else:
            self.cart[product_id] = {'quantity': quantity}

        self.session.modified = True
        self.save_user_cart()

    def save_user_cart(self):
        if self.request.user.is_authenticated:
            current_user = Profile.objects.filter(user__id=self.request.user.id)
            carty = str(self.cart)
            carty = carty.replace("\'", "\"")
            current_user.update(old_cart=str(carty))

    def get_subtotal(self):
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids)
        subtotal = Decimal('0.00')

        for key, value in self.cart.items():
            key = int(key)
            quantity = int(value['quantity'])
            for product in products:
                if product.id == key:
                    subtotal += product.price * quantity

        return subtotal

    def __len__(self):
        return sum(item['quantity'] for item in self.cart.values())

    def get_products(self):
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids)
        return products

    def get_quantities(self):
        quantities = {key: value['quantity'] for key, value in self.cart.items()}
        return quantities

    def update(self, product, quantity):
        product_id = str(product.id)
        if product_id in self.cart:
            # Update the quantity in the cart
            self.cart[product_id]['quantity'] = quantity

        self.session.modified = True
        self.save_user_cart()


    def delete(self, product):
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]

        self.session.modified = True
        self.save_user_cart()

    def clear(self):
        self.cart = {}
        self.session.modified = True
        self.save_user_cart()
