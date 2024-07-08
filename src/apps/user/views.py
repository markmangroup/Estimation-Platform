from typing import Any
from django.http import HttpRequest
from django.http.response import HttpResponse as HttpResponse
from django.shortcuts import redirect
from django.views.generic import FormView
from .forms import LoginForm
from django.contrib.auth import logout
from django.views.generic.base import View


class LoginView(FormView):
    template_name = 'proposal/login.html'
    form_class = LoginForm
    success_url = '/choose_screens'

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        if request.user.is_authenticated:
            return redirect(self.success_url)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.get_user()
        if user:
            from django.contrib.auth import login
            login(self.request, user)
            return super().form_valid(form)
        else:
            return self.form_invalid(form)

class LogoutView(View):
    def get(self, request, *args, **kwargs):
        logout(request)
        return redirect('/')