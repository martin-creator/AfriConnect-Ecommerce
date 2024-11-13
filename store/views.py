from django.shortcuts import render, redirect
from .models import Product, Category, Profile
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .forms import ProfilePhotoForm, SignUpForm, UpdateUserForm, ChangePasswordForm, UserInfoForm

from payment.forms import ShippingForm
from payment.models import ShippingAddress

from django import forms
from django.db.models import Q
import json
from cart.cart import Cart
from django.views.generic import ListView, DetailView


from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView
from .models import Product, Category



class ProductDetailView(DetailView):
    model = Product
    template_name = 'store/product_detail.html'  # Specify your template name here
    context_object_name = 'product'  # Default is 'object'


class ProductListView(ListView):
    model = Product
    template_name = 'product_list.html'
    context_object_name = 'products'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(name__in=['Programming Books', 'Marketing Books'])
        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get('search', '')
        category_id = self.request.GET.get('category', '')

        if search_query:
            queryset = queryset.filter(name__icontains=search_query)
        
        if category_id:
            queryset = queryset.filter(category_id=category_id)

        return queryset

    
def search(request):
	# Determine if they filled out the form
	if request.method == "POST":
		searched = request.POST['searched']
		# Query The Products DB Model
		searched = Product.objects.filter(Q(name__icontains=searched) | Q(description__icontains=searched))
		# Test for null
		if not searched:
			messages.success(request, "That Product Does Not Exist...Please try Again.")
			return render(request, "search.html", {})
		else:
			return render(request, "search.html", {'searched':searched})
	else:
		return render(request, "search.html", {})	


def update_info(request):
	if request.user.is_authenticated:
		# Get Current User
		current_user = Profile.objects.get(user__id=request.user.id)
		# Get Current User's Shipping Info
		shipping_user = ShippingAddress.objects.get(user__id=request.user.id)
		
		# Get original User Form
		form = UserInfoForm(request.POST or None, instance=current_user)
		# Get User's Shipping Form
		shipping_form = ShippingForm(request.POST or None, instance=shipping_user)		
		if form.is_valid() or shipping_form.is_valid():
			# Save original form
			form.save()
			# Save shipping form
			shipping_form.save()

			messages.success(request, "Your Info Has Been Updated!!")
			return redirect('home')
		return render(request, "update_info.html", {'form':form, 'shipping_form':shipping_form})
	else:
		messages.success(request, "You Must Be Logged In To Access That Page!!")
		return redirect('home')



def password_reset(request):
	if request.user.is_authenticated:
		current_user = request.user
		# Did they fill out the form
		if request.method  == 'POST':
			form = ChangePasswordForm(current_user, request.POST)
			# Is the form valid
			if form.is_valid():
				form.save()
				messages.success(request, "Your Password Has Been Updated...")
				login(request, current_user)
				return redirect('update_user')
			else:
				for error in list(form.errors.values()):
					messages.error(request, error)
					return redirect('update_password')
		else:
			form = ChangePasswordForm(current_user)
			return render(request, "update_password.html", {'form':form})
	else:
		messages.success(request, "You Must Be Logged In To View That Page...")
		return redirect('home')
def update_user(request):
	if request.user.is_authenticated:
		current_user = User.objects.get(id=request.user.id)
		user_form = UpdateUserForm(request.POST or None, instance=current_user)

		if user_form.is_valid():
			user_form.save()

			login(request, current_user)
			messages.success(request, "User Has Been Updated!!")
			return redirect('home')
		return render(request, "update_user.html", {'user_form':user_form})
	else:
		messages.success(request, "You Must Be Logged In To Access That Page!!")
		return redirect('home')


def category_summary(request):
	categories = Category.objects.all()
	return render(request, 'category_summary.html', {"categories":categories})	

def category(request, category):
	# Replace Hyphens with Spaces
	category = category.replace('-', ' ')
	# Grab the category from the url
	try:
		# Look Up The Category
		category = Category.objects.get(name=category)
		products = Product.objects.filter(category=category)
		return render(request, 'category.html', {'products':products, 'category':category})
	except Category.DoesNotExist:
		messages.success(request, ("That Category Doesn't Exist..."))
		return redirect('home')


def product(request,pk):
	product = Product.objects.get(id=pk)
	return render(request, 'product.html', {'product':product})


def home(request):
	products = Product.objects.all()
	return render(request, 'home.html', {'products':products})


def about(request):
	return render(request, 'about.html', {})

from django.contrib.auth.decorators import login_required

@login_required
def profile(request):
    return render(request, 'profile.html')

def orders(request):
    return render(request, 'orders.html')

def login_user(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, "You Have Been Logged In!")
            return redirect('profile')
        else:
            messages.error(request, "There was an error, please try again...")
    return render(request, 'login.html', {})


def logout_user(request):
	logout(request)
	messages.success(request, ("You have been logged out...Thanks for stopping by..."))
	return redirect('home')



def register_user(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            phone = form.cleaned_data.get('phone')
            address1 = form.cleaned_data.get('address1')
            address2 = form.cleaned_data.get('address2')
            city = form.cleaned_data.get('city')
            state = form.cleaned_data.get('state')
            zipcode = form.cleaned_data.get('zipcode')
            country = form.cleaned_data.get('country')

            try:
                # Create a profile for the new user
                profile, created = Profile.objects.get_or_create(
                    user=user,
                    defaults={
                        'phone': phone,
                        'address1': address1,
                        'address2': address2,
                        'city': city,
                        'state': state,
                        'zipcode': zipcode,
                        'country': country,
                    }
                )
                if created:
                    print('Profile created for user')
                else:
                    print('Profile already exists for user')
                    
                login(request, user)  # Log the user in after registration
                return redirect('profile')  # Redirect to profile page
            except IntegrityError:
                form.add_error(None, 'A profile already exists for this user.')
                return render(request, 'register.html', {'form': form, 'error': 'A profile already exists for this user.'})
        else:
            print(form.errors)  # Print form errors to the console for debugging
            return render(request, 'register.html', {'form': form, 'error': 'Whoops! There was a problem Registering, please try again...'})
    else:
        form = SignUpForm()
    return render(request, 'register.html', {'form': form})
