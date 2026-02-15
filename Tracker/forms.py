from django import forms
from django.core.exceptions import ValidationError

from .models import Transaction, Category, Budget, Wallet


def _add_bootstrap_classes(form: forms.Form):
    """
    Adds Bootstrap classes to all fields so templates stay clean.
    """
    for name, field in form.fields.items():
        widget = field.widget

        # base classes
        classes = widget.attrs.get("class", "")

        # select vs input/textarea
        if isinstance(widget, forms.Select):
            base = "form-select"
        else:
            base = "form-control"

        # keep small sizing consistent
        base += " form-control-sm" if base == "form-control" else " form-select-sm"

        widget.attrs["class"] = f"{classes} {base}".strip()

        # helpful placeholders
        if name == "amount":
            widget.attrs.setdefault("placeholder", "e.g. 1500")
        if name == "note":
            widget.attrs.setdefault("placeholder", "e.g. lunch, rent, salary...")


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _add_bootstrap_classes(self)


class BudgetForm(forms.ModelForm):
    class Meta:
        model = Budget
        fields = ["category", "month", "limit_amount"]
        widgets = {
            "month": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        if self.user:
            self.fields["category"].queryset = Category.objects.filter(owner=self.user)

        _add_bootstrap_classes(self)

    def clean_category(self):
        cat = self.cleaned_data.get("category")
        if cat and (self.user is None or cat.owner != self.user):
            raise ValidationError("Invalid category selection.")
        return cat


class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ["wallet", "t_type", "amount", "category", "date", "note"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        if self.user is not None:
            self.fields["category"].queryset = Category.objects.filter(owner=self.user)
            self.fields["wallet"].queryset = Wallet.objects.filter(owner=self.user)

        _add_bootstrap_classes(self)

    def clean_amount(self):
        amount = self.cleaned_data.get("amount")
        if amount is not None and amount <= 0:
            raise ValidationError("Amount must be greater than 0.")
        return amount

    def clean_category(self):
        cat = self.cleaned_data.get("category")
        if cat and (self.user is None or cat.owner != self.user):
            raise ValidationError("Invalid category selection.")
        return cat

    def clean_wallet(self):
        wallet = self.cleaned_data.get("wallet")
        if wallet and (self.user is None or wallet.owner != self.user):
            raise ValidationError("Invalid wallet selection.")
        return wallet
