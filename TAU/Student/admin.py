

# Register your models here.
from django.contrib import admin
from .models import Complaint
from django.utils.html import format_html

class ComplaintAdmin(admin.ModelAdmin):
    list_display = ('ticket_id', 'department', 'short_description', 'attachment_link', 'status')
    readonly_fields = ('ticket_id', 'attachment_link')

    def short_description(self, obj):
        # Show a shortened version of the description
        return (obj.description[:50] + '...') if len(obj.description) > 50 else obj.description
    short_description.short_description = 'Description'

    def attachment_link(self, obj):
        if obj.attachment:
            return format_html('<a href="{}" target="_blank">View</a>', obj.attachment.url)
        return "No attachment"
    attachment_link.short_description = 'Attachment'

admin.site.register(Complaint, ComplaintAdmin)
