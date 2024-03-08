from django.contrib import admin

from . import models


admin.site.register(models.Art)
admin.site.register(models.ArtComment)
admin.site.register(models.ArtLike)
