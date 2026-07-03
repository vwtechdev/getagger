from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth import views as auth_views
from django.shortcuts import redirect, render

from apps.accounts.forms import LoginForm, SignupForm


class LoginView(auth_views.LoginView):
    authentication_form = LoginForm
    template_name = 'accounts/login.html'


class LogoutView(auth_views.LogoutView):
    next_page = 'login'


def signup(request):
    """Auto-registro do técnico (RF-02)."""
    if request.user.is_authenticated:
        return redirect('services:service_call_list')
    form = SignupForm(request.POST or None)
    if form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, f'Conta criada. Bem-vindo, {user.name}.')
        return redirect('services:service_call_list')
    return render(request, 'accounts/signup.html', {'form': form})
