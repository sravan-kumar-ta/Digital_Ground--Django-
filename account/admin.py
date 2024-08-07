from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

from account.models import Address


class CustomUserAdmin(UserAdmin):
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (
            _('Personal info'),
            {
                'fields': (
                    'first_name',
                    'last_name',
                    'username',
                    'phone_number'
                ),
            },
        ),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser',)}),
    )

    list_display = ('username', 'email', 'phone_number', 'is_active', 'is_staff')
    list_filter = ('is_staff', 'is_active',)
    filter_horizontal = ()


admin.site.register(get_user_model(), CustomUserAdmin)
admin.site.register(Address)
