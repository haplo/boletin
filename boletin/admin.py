# -*- coding: utf-8 -*-
from django.contrib import admin


class NewsletterModelAdmin(admin.ModelAdmin):
    date_hierarchy = 'date'
    fields = ('text_content', 'html_content', 'reviewed', 'pending', )
    list_display = ('number', 'period', 'date', 'date_created', 'reviewed', 'pending', )
    list_filter = ('period', 'reviewed', 'pending', )
    ordering = ('-date', )
    search_fields = ('text_content', 'html_content', )

    def has_add_permission(self, request):
        return False


class NewsletterSubscriptionModelAdmin(admin.ModelAdmin):
    date_hierarchy = 'subscription_date'
    list_display = ('email', 'period', 'confirmed', 'hashkey', )
    list_filter = ('period', 'confirmed', )
    ordering = ('-subscription_date', )
    radio_fields = {'period': admin.HORIZONTAL}
    search_fields = ('email', )
