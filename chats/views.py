from django.shortcuts import render


def index_view(request):
    context = {}
    return render(request, 'chats/index.html', context)


def my_profile_view(request):
    context = {}
    return render(request, 'chats/my_profile.html', context)
