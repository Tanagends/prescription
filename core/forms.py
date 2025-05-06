# core/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User

class CustomUserCreationForm(UserCreationForm):
    # Add any extra fields you want on your registration form
    # For example, first_name, last_name, and your custom 'role' field
    role = forms.ChoiceField(choices=User.ROLE_CHOICES, required=True)
    first_name = forms.CharField(max_length=30, required=False, help_text='Optional.')
    last_name = forms.CharField(max_length=150, required=False, help_text='Optional.')
    # phone_number = forms.CharField(max_length=20, required=False) # Add if you want it at registration

    class Meta(UserCreationForm.Meta):
        model = User
        # Your USERNAME_FIELD is 'email'.
        # UserCreationForm already includes password fields.
        # 'username' is still technically required by AbstractUser for createsuperuser and some internal Django things.
        # You can choose to ask for it, or set it programmatically in the view (e.g., to be the same as email).
        # For simplicity, we'll include it here. If you don't want users to set a separate username,
        # you can remove it and handle it in the view.
        fields = ('username', 'email', 'first_name', 'last_name', 'role')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = self.cleaned_data['role']
        # If you didn't ask for 'username' in the form but need to set it:
        # if not user.username:
        #     user.username = self.cleaned_data['email'] # Or generate a unique username
        if commit:
            user.save()
        return user

class CustomAuthenticationForm(AuthenticationForm):
    # The default AuthenticationForm uses 'username' as the field name.
    # Since your USERNAME_FIELD is 'email', users will type their email into the 'username' field.
    # This form customization is mostly for changing the label if desired.
    username = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={'autofocus': True})
    )
    # You could also override error messages or add more custom validation if needed
