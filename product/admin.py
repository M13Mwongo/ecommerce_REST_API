from django.contrib import admin
from .models import Product

# Register your models here.


class ProductAdmin(admin.ModelAdmin):
    # fieldsets = [
    #     ("SU Information", {"fields": ["student_number", "email"]}),
    #     ('Student Information', {"fields": [
    #         "first_name", "last_name",  "phone_number", 'fun_fact']})
    # ]
    search_fields = ['name', 'brand', 'category', 'price', 'rating']
    list_display = ['name', 'category', 'price', 'stock']
    list_filter = ['category', 'brand']
    # readonly_fields = ("email",)


admin.site.register(Product, ProductAdmin)
