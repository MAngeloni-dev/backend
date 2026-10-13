from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = (
        "username",
        "first_name",
        "last_name",
        "email",
        "rol",
        "is_active",
        "is_staff",
    )

    list_filter = UserAdmin.list_filter + ("rol",)

    fieldsets = UserAdmin.fieldsets + (
        ("Rol en el CRM", {"fields": ("rol",)}),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Rol en el CRM", {"fields": ("rol",)}),
    )