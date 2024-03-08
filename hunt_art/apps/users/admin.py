from django.contrib import admin

from . import models


admin.site.register(models.User)


class PriceListImageInline(admin.TabularInline):
    model = models.PriceListImage
    extra = 0


@admin.register(models.UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    inlines = (
        PriceListImageInline,
    )
