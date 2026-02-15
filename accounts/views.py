from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.contrib.auth.forms import UserCreationForm


class SignUpView(CreateView):
    form_class = UserCreationForm
    template_name = "registration/signup.html"
    success_url = reverse_lazy("login")

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        # Remove default help texts
        for field in form.fields.values():
            field.help_text = ""

        return form
