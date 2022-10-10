from django.contrib import admin
from dashboard.models import KPICostsMatrixResults,KPIScalarResults,AssetsResults, KPIScalarMatrixResults

admin.site.register(KPICostsMatrixResults)
admin.site.register(KPIScalarMatrixResults)
admin.site.register(KPIScalarResults)

@admin.register(AssetsResults)
class AssetsResultsAdmin(admin.ModelAdmin):
    list_display = ["id", "simulation"]