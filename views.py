from django.contrib.auth.mixins import PermissionRequiredMixin

from django.conf import settings
import requests
from django.http import HttpResponse
import json
from sdc_people.models import Person
from django.views.generic.list import ListView
from django.shortcuts import render
from datetime import date

def email_list(request):

    people_no_email = []
    all_emails = {}
    emails_not_in_brevo = {}
    emails_brevo_match = {}
    emails_brevo_mismatch = {}
    brevo_not_in_db = {}

    people = Person.objects.all().order_by('primary_email')

    brevo_url = settings.BREVO_CONTACTS_URL
    brevo_headers = settings.BREVO_CONTACTS_HEADERS

    response_brevo = requests.get(brevo_url, headers=brevo_headers)
    contacts_json = json.loads(response_brevo.content)['contacts']


    for person in people:
        primary_email = person.primary_email
        if primary_email is None or primary_email == '':
            people_no_email.append(person)
        else:
            if primary_email not in all_emails:
                all_emails[primary_email] = {'people': [ person ], 'membership_class': [ person.membershipclass.name ] }
            else:
                all_emails[primary_email]['people'].append( person )
                all_emails[primary_email]['membership_class'].append( person.membershipclass.name )


    for contact_json in contacts_json:
        try:
            key_email = contact_json["email"].lower()
            if key_email in all_emails:
                all_emails[ key_email ]['brevo_contact']=contact_json
                all_emails[ key_email ]['brevo_membership_class'] = contact_json['attributes']['MEMBERSHIP_CLASS']
                if all_emails[ key_email ]['membership_class'] == contact_json['attributes']['MEMBERSHIP_CLASS']:
                    emails_brevo_match[ key_email ] = all_emails[ key_email ]
                else:
                    emails_brevo_mismatch[ key_email ] = all_emails[ key_email ]
            else:
                brevo_not_in_db[ key_email ] = contact_json

        except KeyError:
            continue

    for email in all_emails:
        if 'brevo_contact' not in all_emails[ email ]:
            emails_not_in_brevo[ email ] = all_emails[ email ]


    content = {
        'all_emails': all_emails,
        'emails_not_in_brevo': emails_not_in_brevo,
        'emails_brevo_mismatch': emails_brevo_mismatch,
        'emails_brevo_match': emails_brevo_match,
        'brevo_not_in_db': brevo_not_in_db,
        'people_no_email': people_no_email,
    }


    return render( request, "sdc_brevo/email_list.html", content )



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



