from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

User = get_user_model()


class RegisterForm(UserCreationForm):
    first_name = forms.CharField(label="Họ và tên", max_length=150)
    email = forms.EmailField(label="Email")

    class Meta:
        model = User
        fields = ("username", "first_name", "email", "password1", "password2")