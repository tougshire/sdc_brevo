from django.urls import path, reverse_lazy
from django.views.generic.base import RedirectView

from . import views

app_name = "sdc_brevo"

urlpatterns = [

    path(
        "",
        RedirectView.as_view(url=reverse_lazy("sdc_brevo:email-list")),
    ),
    path(
        "email/list/",
        views.email_list,
        name="email-list",
    ),

]
