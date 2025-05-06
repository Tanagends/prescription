from django.shortcuts import render

# Create your views here.

# core/views.py

from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView
from django.contrib.auth import login
from django.contrib.auth.views import LoginView as AuthLoginView # Renaming to avoid clash
from .forms import CustomUserCreationForm, CustomAuthenticationForm

class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('login') # Redirect to login page after successful registration
    template_name = 'registration/signup.html'

    def form_valid(self, form):
        response = super().form_valid(form)
        # Optionally, log the user in directly after registration
        # user = form.save()
        # login(self.request, user)
        # self.success_url = reverse_lazy('home') # Redirect to home if logged in
        return response

# You can use Django's built-in LoginView, but if you want to use your CustomAuthenticationForm by default:
class CustomLoginView(AuthLoginView):
    form_class = CustomAuthenticationForm
    template_name = 'registration/login.html'
    # success_url will be LOGIN_REDIRECT_URL from settings.py by default
