from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .services import NUMBER_COUNT, validate_numbers


class SignupForm(UserCreationForm):
    email = forms.EmailField(required=False, label="이메일")

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]
        labels = {
            "username": "아이디",
        }


class ManualTicketForm(forms.Form):
    number_1 = forms.IntegerField(min_value=1, max_value=45, label="번호 1")
    number_2 = forms.IntegerField(min_value=1, max_value=45, label="번호 2")
    number_3 = forms.IntegerField(min_value=1, max_value=45, label="번호 3")
    number_4 = forms.IntegerField(min_value=1, max_value=45, label="번호 4")
    number_5 = forms.IntegerField(min_value=1, max_value=45, label="번호 5")
    number_6 = forms.IntegerField(min_value=1, max_value=45, label="번호 6")

    def clean(self):
        cleaned_data = super().clean()
        raw_numbers = [cleaned_data.get(f"number_{index}") for index in range(1, NUMBER_COUNT + 1)]
        if any(number is None for number in raw_numbers):
            return cleaned_data
        try:
            cleaned_data["numbers"] = validate_numbers(raw_numbers)
        except ValueError as exc:
            raise forms.ValidationError(str(exc)) from exc
        return cleaned_data


class AutoTicketForm(forms.Form):
    quantity = forms.IntegerField(min_value=1, max_value=5, initial=1, label="구매 수량")
