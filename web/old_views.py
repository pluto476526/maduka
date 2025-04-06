from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.db.models import Q
from shop.models import Shop, ShopCategory
from dash.models import Profile, Category
from web.forms import UserRegistrationForm
import logging



# Get logger
# logger.debug()
logger = logging.getLogger(__name__)



def home(request):
    if request.method == 'POST':
        owner = request.user
        name = request.POST.get('name')
        bio = request.POST.get('bio')
        category = request.POST.get('category')
        source = request.POST.get('source')

        if request.user.is_authenticated:
            profile = get_object_or_404(Profile, user=request.user)
            logger.debug(f'web prof: {profile}')

            if source == 'new_shop':
                category_instance = get_object_or_404(ShopCategory, category=category)
                Shop.objects.create(
                    owner = owner,
                    name = name,
                    bio = bio,
                    shop_category = category_instance,
                )
                shop = get_object_or_404(Shop, owner=request.user)
                profile.shop = shop
                profile.save()
                messages.success(request, f'{name} registered')
                return redirect('home')

        else:
            profile = None

    shops = Shop.objects.all()
    shop_categories = ShopCategory.objects.all()

    context = {
        'available_shops': shops,
        'shop_categories': shop_categories,
        'profile': profile,
    }
    return render(request, 'web/index.html', context)


def register(request):
    register_form = UserRegistrationForm()

    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        register_form = UserRegistrationForm(request.POST)

        if register_form.is_valid():
            register_form.save()
            return redirect('sign_in')

    context = {
        'register_form': register_form,
    }
    return render(request, 'web/register.html', context)


def sign_in(request):
    login_form = AuthenticationForm()

    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        try:
            user = authenticate(request, username=username, password=password)

            if user is None:
                messages.error(request, 'Invalid username or password')

            else:
                logger.debug(f"Authenticated user: {user}")

                if not hasattr(user, 'profile'):
                    Profile.objects.create(user=user)

                login(request, user)
                return redirect('home')
            
        except Exception as e:
            logger.error(f"An error occurred: {e}")

    context = {'login_form': login_form}
    return render(request, 'web/sign_in.html', context)


def sign_out(request):
    logger.debug(f"Logged out user: {request.user}")
    logout(request)
    return redirect('home')


def all_shops_view(request):
    logger.debug(f'all shops')
    # all_shops = Shop.objects.exclude(owner=request.user)
    all_shops = Shop.objects.all()
    logger.debug(all_shops)
    logger.debug(f'fack')

    q = request.GET.get('q')

    if q:
        all_shops = all_shops.filter(
            Q(name__icontains=q) |
            Q(shop_category__category__icontains=q) |
            Q(owner__username__icontains=q)
        )

    context = {
        'all_shops': all_shops,
    }
    return render(request, 'web/all_shops.html', context)


def shop_details_view(request, name):
    selected_shop = get_object_or_404(Shop, name=name)
    categories = Category.objects.filter(shop=selected_shop.id)
    context = {
        'selected_shop': selected_shop,
        'categories': categories,
    }
    return render(request, 'web/shop_details.html', context)






