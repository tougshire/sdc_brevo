from django.urls import path, reverse_lazy
from django.views.generic.base import RedirectView

from . import views

app_name = "sdc_brevo"

urlpatterns = [

    path(
        "person/list/",
        views.PersonList.as_view(),
        name="person-list",
    ),

]
