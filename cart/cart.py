from decimal import Decimal
from django.conf import settings
from store.models import Product

class Cart(object):
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart

    def add(self, product, quantity=1):
        product_id = str(product.id)
        if product_id not in self.cart:
            self.cart[product_id] = {'quantity': 0, 'price': str(product.price)}  # Store price as string
        self.cart[product_id]['quantity'] += quantity
        self.save()

    def save(self):
        self.session[settings.CART_SESSION_ID] = self.cart
        self.session.modified = True

    def remove(self, product):
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def get_products(self):
        # Convert the stored price back to Decimal to handle it correctly
        products = []
        for product_id, item in self.cart.items():
            product = Product.objects.get(id=product_id)
            item['price'] = Decimal(item['price'])  # Convert price back to Decimal
            products.append(product)
        return products

    def get_quantities(self):
        return {product_id: item['quantity'] for product_id, item in self.cart.items()}

    def get_subtotal(self):
        subtotal = Decimal('0.00')
        for product_id, item in self.cart.items():
            product = Product.objects.get(id=product_id)
            subtotal += item['quantity'] * Decimal(item['price'])
        return subtotal

    def clear(self):
        del self.session[settings.CART_SESSION_ID]
        self.session.modified = True

    def __iter__(self):
        for product_id, item in self.cart.items():
            product = Product.objects.get(id=product_id)
            item['price'] = Decimal(item['price'])  # Ensure price is Decimal
            yield product, item
            
    # Implementing __len__ to return the number of items in the cart
    def __len__(self):
        return sum(item['quantity'] for item in self.cart.values())
    
    def update(self, product, quantity):
        product_id = str(product.id)
        if product_id in self.cart:
            self.cart[product_id]['quantity'] = quantity
        self.save()