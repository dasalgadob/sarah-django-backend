"""Admin registrations for the core app."""

from django.contrib import admin
from django.contrib.auth.models import User

from .models import Role, Company

admin.site.register(Role)
admin.site.register(Company)
