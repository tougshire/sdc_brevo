from django.contrib.auth.mixins import PermissionRequiredMixin

from django.conf import settings
import requests
from django.http import HttpResponse
import json
from sdc_people.models import Person
from django.views.generic.list import ListView
from datetime import date

class PersonList(PermissionRequiredMixin, ListView):

    permission_required = "sdc_people.view_person"
    model = Person
    template_name = "sdc_brevo/person_list.html"

    def get_context_data(self, *args, **kwargs):

        context_data=super().get_context_data(*args, **kwargs)

        context_data["person_labels"] = {
            field.name: field.verbose_name.title()
            for field in Person._meta.get_fields()
            if type(field).__name__[-3:] != "Rel"
        }

        url = settings.BREVO_CONTACTS_URL
        headers = settings.BREVO_CONTACTS_HEADERS 
        
        response = requests.get(url, headers=headers)
        contacts_json = json.loads(response.content)
        brevo_contacts_byemail = {}
        non_contacts = []
        dif_contacts = []
        non_emails = []
        to_brevo = {}

        for contact_json in contacts_json["contacts"]:
            try:
                key_email = contact_json["email"].lower()
                brevo_contacts_byemail[key_email]={
                    'id':contact_json["id"],
                    'membership_class':[]
                }
            except KeyError:
                continue
            try:
                brevo_contacts_byemail[key_email]["membership_class" ] = contact_json["attributes"]["MEMBERSHIP_CLASS"]
            except KeyError:
                pass
            

        for person in Person.objects.all().order_by("-membership_date"):
            if not person.primary_email:
                non_emails.append(person)
            elif person.primary_email.lower() not in brevo_contacts_byemail:
                    non_contacts.append(person)
            else:
                if person.membershipclass.name not in brevo_contacts_byemail[person.primary_email.lower()]["membership_class"] or len(brevo_contacts_byemail[person.primary_email.lower()]["membership_class"]) != 1:
                    to_brevo={
                        "id":brevo_contacts_byemail[person.primary_email.lower()]["id"],
                        "membership_class":[]
                    }
                    try:
                        to_brevo["membership_class"] = brevo_contacts_byemail[person.primary_email.lower()]["membership_class"]
                    except KeyError:
                        pass

                    setattr(person, "to_brevo", to_brevo)

                    dif_contacts.append(person)

        context_data["non_emails"] = non_emails
        context_data["dif_contacts"] = dif_contacts
        context_data["non_contacts"] = non_contacts

        return context_data


    
