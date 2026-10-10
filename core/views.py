from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout


def home(request):

    return render(
        request,
        'core/home.html'
    )


# =========================
# REGISTER
# =========================

def register(request):

    if request.method == 'POST':

        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')


        if password != confirm_password:

            return render(
                request,
                'core/register.html',
                {
                    'error': 'Passwords do not match.'
                }
            )


        if User.objects.filter(
            username=username
        ).exists():

            return render(
                request,
                'core/register.html',
                {
                    'error': 'Username already exists.'
                }
            )


        user = User.objects.create_user(

            username=username,

            email=email,

            password=password
        )


        login(
            request,
            user
        )


        return redirect('home')


    return render(
        request,
        'core/register.html'
    )


# =========================
# LOGIN
# =========================

def user_login(request):

    if request.method == 'POST':

        username = request.POST.get('username')

        password = request.POST.get('password')


        user = authenticate(
            request,
            username=username,
            password=password
        )


        if user is not None:

            login(
                request,
                user
            )

            return redirect('home')


        return render(
            request,
            'core/login.html',
            {
                'error': 'Invalid username or password.'
            }
        )


    return render(
        request,
        'core/login.html'
    )


# =========================
# LOGOUT
# =========================

def user_logout(request):

    logout(request)

    return redirect('home')