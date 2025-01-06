# Copyright 2024-2025 Laurent Defert
#
#  This file is part of SOSSE.
#
# SOSSE is free software: you can redistribute it and/or modify it under the terms of the GNU Affero
# General Public License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# SOSSE is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even
# the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License along with SOSSE.
# If not, see <https://www.gnu.org/licenses/>.

from http.cookiejar import MozillaCookieJar
from io import StringIO

from django import forms
from django.contrib import messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, reverse
from django.views.generic import FormView

from .models import Cookie
from .views import UserView


class CookieForm(forms.Form):
    cookies = forms.CharField(
        label="Cookies",
        widget=forms.Textarea(attrs={"placeholder": "Enter cookies here..."}),
        required=False,
    )
    cookies.widget.attrs.update({"style": "width: 50%; padding-right: 0"})
    cookies_file = forms.FileField(required=False)

    def clean(self):
        self.cleaned_data = super().clean()
        if (self.cleaned_data.get("cookies") and self.cleaned_data.get("cookies_file")) or not (
            self.cleaned_data.get("cookies") or self.cleaned_data.get("cookies_file")
        ):
            raise ValidationError("Cookies should either be entered in the text field, or provided as a file")

        cookies = self.cleaned_data.get("cookies")
        if not cookies:
            cookies = self.cleaned_data["cookies_file"].read()
            cookies = cookies.decode("utf-8")

        jar = MozillaCookieJar()
        cookie_io = StringIO(cookies.replace("\r", "\n"))

        try:
            jar._really_load(cookie_io, "Input buffer", True, True)
        except Exception as e:
            raise ValidationError(f"Failed to load cookies: {str(e)}")
        self.cleaned_data["cookies"] = jar
        return self.cleaned_data


class CookiesImportView(UserView, FormView):
    template_name = "admin/cookies_import.html"
    title = "Cookies import"
    form_class = CookieForm

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        if not request.user.is_staff or not request.user.is_superuser:
            return redirect(reverse("search"))
        if not request.user.has_perm("se.change_cookie"):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        cookie_jar = form.cleaned_data["cookies"]
        Cookie.set_from_jar(None, cookie_jar)
        messages.success(self.request, f"{len(cookie_jar)} cookies loaded.")
        return redirect("admin:se_cookie_changelist")
