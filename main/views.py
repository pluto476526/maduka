from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from main.models import MainHelpDesk
from shop.models import Shop
from web.models import Message
import logging


# Get logger
logger = logging.getLogger(__name__)


def all_shops_view(request):
    shops = Shop.objects.filter(is_banned=False)
    context = {
        'valid_shops': shops,
    }
    return render(request, 'main/all_shops.html', context)


def pending_applications_view(request):
    shops = Shop.objects.filter(status='pending')
    context = {
        'valid_shops': shops,
    }
    return render(request, 'main/pending_shops.html', context)


def shop_profile_view(request, shop_name):
    shop = get_object_or_404(Shop, name=shop_name)

    if request.method == 'POST':
        is_featured = request.POST.get('is_featured')
        is_banned = request.POST.get('is_banned')
        source = request.POST.get('source')

        if source == 'settings_form':
            if is_featured:
                shop.is_featured = True

            else:
                shop.is_featured = False

            if is_banned:
                shop.is_banned = True

            else:
                shop.is_banned = False

        logger.debug(shop.is_banned)
        shop.save()
        messages.success(request, 'Shop settings edited.')
        return redirect('main_shop_profile', shop.name)

    context = {'shop': shop}
    return render(request, 'main/shop_profile.html', context)



def helpdesk_view(request):
    tickets = MainHelpDesk.objects.all()
    pending_tickets = tickets.filter(is_sorted=False)
    sorted_tickets = tickets.filter(is_sorted=True)

    if request.method == 'POST':
        status = request.POST.get('status').lower()
        is_sorted = request.POST.get('is_sorted')
        tkt_id = request.POST.get('id')
        source = request.POST.get('source')

        if source == 'change_status':
            ticket = get_object_or_404(MainHelpDesk, id=tkt_id)
            ticket.status = status

            if is_sorted:
                ticket.is_sorted = True
                ticket.status = 'sorted'

            ticket.admin = request.user
            ticket.save()
            messages.success(request, f'Iicket ID: {ticket.help_id} Status: {ticket.status}')
            return redirect('main_helpdesk')

    context = {
        'pending_tickets': pending_tickets,
        'sorted_tickets': sorted_tickets,
    }
    return render(request, 'main/helpdesk.html', context)


def messages_view(request):
    rec_messages = Message.objects.all()
    context = {
        'rec_messages': rec_messages,
    }
    return render(request, 'main/messages.html', context)
