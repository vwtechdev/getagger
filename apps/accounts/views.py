from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth import views as auth_views
from django.shortcuts import redirect, render

from apps.accounts.forms import LoginForm, SignupForm


class LoginView(auth_views.LoginView):
    authentication_form = LoginForm
    template_name = 'accounts/login.html'

    def form_valid(self, form):
        user = form.get_user()
        if not user.is_active:
            return redirect('accounts:pending_approval')
        login(self.request, user)
        return super().form_valid(form)


def pending_approval(request):
    return render(request, 'accounts/pending_approval.html')


class LogoutView(auth_views.LogoutView):
    next_page = 'login'


def signup(request):
    """Auto-registro do técnico (RF-02)."""
    if request.user.is_authenticated:
        return redirect('services:service_call_list')
    form = SignupForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Conta criada. Aguarde aprovação do administrador para acessar.')
        return redirect('login')
    return render(request, 'accounts/signup.html', {'form': form})
