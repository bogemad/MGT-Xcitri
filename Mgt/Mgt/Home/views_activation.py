# Home/views_activation.py

from django.shortcuts import redirect
from django.urls import reverse
from django_registration.backends.activation.views import ActivationView as BaseActivationView

class AutoActivationView(BaseActivationView):
    """
    Immediately activates the user on GET, skipping the form.
    """
    def get(self, request, *args, **kwargs):
        key = request.GET.get(self.activation_key_parameter, "")
        user = self.activate(request, key)
        if user:
            return redirect(reverse("django_registration_activation_complete"))
        return super().get(request, *args, **kwargs)
    