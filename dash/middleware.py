import re, logging
from django.shortcuts import get_object_or_404
from django.utils.timezone import now
from dash.models import HomePageSession
from dash.context_processors import my_shop
from shop.models import Shop


logger = logging.getLogger(__name__)

class HomePageSessionTrackerMiddleware:
    SHOP_PATH_REGEX = re.compile(r"^/shop/(?P<shopname>[\w-]+)/$")

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        match = self.SHOP_PATH_REGEX.match(request.path)

        if match:
            shop_slug = match.group('shopname')
            session_flag = f'has_visited_shop_{shop_slug}'

            # Check if the user has already visited the shop in this session
            if not request.session.get(session_flag):
                request.session[session_flag] = True

                # Ensure session key is created if it doesn't exist
                if not request.session.session_key:
                    request.session.save()

                sessionID = request.session.session_key
                user_agent = request.META.get('HTTP_USER_AGENT')
                ip_addr = self.get_client_ip(request)

                # Fetch the shop using the shop_slug
                shop = get_object_or_404(Shop, slug=shop_slug)
                
                # Prevent duplicate session records by checking if a record already exists
                if not HomePageSession.objects.filter(shop=shop, sessionID=sessionID).exists():
                    HomePageSession.objects.create(
                        shop=shop,
                        sessionID=sessionID,
                        user_agent=user_agent,
                        ip_addr=ip_addr,
                    )

        return self.get_response(request)

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class SessionExitTrackerMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        sessionID = request.session.session_key

        if sessionID:
            try:
                # Attempt to retrieve the session from the DB
                sesh = HomePageSession.objects.filter(sessionID=sessionID).last()
                sesh.exit_time = now()
                sesh.save(update_fields=['exit_time'])
            except HomePageSession.DoesNotExist:
                pass
            except Exception:
                pass

        return response
