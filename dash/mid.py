# dash/middleware.py

from django.shortcuts import get_object_or_404
from django.utils.timezone import now
from dash import models, context_processors
import re


class HomePageSessionTrackerMiddleware:
    SHOP_PATH_REGEX = re.compile(r"^/shop/(?P<shopname>[\w-]+)/$")
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        match = self.SHOP_PATH_REGEX.match(request.path)

        if match:
            shop_slug = match.group('shopname')
            session_flag = f'has_visited_shop_{shop_slug}'

            if not request.session.get(session_flag):
                request.session[session_flag] = True

                if not request.session.session_key:
                    request.session.save()

                sessionID = request.session.session_key or request.session._get_or_create_session_key()
                user_agent = request.META.get('HTTP_USER_AGENT')
                ip_addr = self.get_client_ip(request)
                shop = context_processors.my_shop(request)

                # if not models.HomePageSession.objects.filter(shop=shop, sessionID=sessionID).exists():
                models.HomePageSession.objects.create(
                    shop = shop,
                    sessionID = sessionID,
                    user_agent = user_agent,
                    ip_addr = ip_addr,
                )
        return self.get_response(request)


    def get_client_ip(self, request):
        x_fowarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_fowarded_for:
            ip = x_fowarded_for.split(',')[0]
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
                sesh = models.HomePageSession.objects.get(sessionID=sessionID)
                sesh.exit_time = now()
                sesh.save(update_fields=['exit_time'])
            except models.HomePageSession.DoesNotExist:
                pass
            # except Exception:
            #    pass
        return response
