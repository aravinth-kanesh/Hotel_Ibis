from django.contrib import admin
from .models import User, Language, Tutor, Student, StudentRequest, Invoice, Lesson, Message, TutorLangRequest, TutorAvailability
# Register your models here.

# Registers the User model with custom admin configuration.
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'role', 'is_active') 
    list_filter = ('role', 'is_active') 
    search_fields = ('username', 'email', 'first_name', 'last_name') 
    ordering = ('last_name', 'first_name')  

# Registers the Language model with custom admin configuration.
@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ('id', 'name') 
    search_fields = ('name',) 
    ordering = ('name',)  

# Registers the Tutor model with custom admin configuration (and with displaying taught languages).
@admin.register(Tutor)
class TutorAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'get_languages') 
    search_fields = ('user__username', 'user__email')  
    autocomplete_fields = ['user']   
    filter_horizontal = ['languages'] 

    def get_languages(self, obj):
        """Display the languages taught by the tutor."""
        return ", ".join([language.name for language in obj.languages.all()])
    get_languages.short_description = 'Languages Taught'

# Registers the Student model with custom admin configuration.
@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('id', 'user') 
    search_fields = ('user__username', 'user__email')  
    autocomplete_fields = ['user']  

# Registers the Invoice model with custom admin configuration (and filtering and date hierarchy).
@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('id', 'student', 'tutor','lessons', 'total_amount', 'paid', 'date_issued', 'date_paid')  
    list_filter = ('paid', 'date_issued')  
    search_fields = ('student__UserID__username', 'tutor__UserID__username')  
    date_hierarchy = 'date_issued' 

# Registers the Lesson model with custom admin configuration (with filtering and autocomplete fields).
@admin.register(Lesson)
class ClassAdmin(admin.ModelAdmin):
    list_display = ('id', 'tutor', 'student', 'language', 'date', 'time', 'venue', 'duration', 'frequency', 'term')
    list_filter = ('frequency', 'term', 'date') 
    search_fields = ('tutor__UserID__username', 'student__UserID__username', 'language__name')  
    autocomplete_fields = ['tutor', 'student', 'language'] 

# Registers the StudentRequest model with custom admin configuration (with filtering and ordering).
@admin.register(StudentRequest)
class StudentRequestAdmin(admin.ModelAdmin):
    list_display = ('student', 'language', 'is_allocated', 'created_at', 'term', 'frequency')  
    list_filter = ('is_allocated', 'term', 'frequency', 'language') 
    search_fields = ('student__UserID__username', 'language__name', 'description') 
    ordering = ('-created_at',)  

# Registers the Message model with custom admin configuration, showing previous messages and replies.
@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """Admin view for the Message model."""
    list_display = ('sender', 'recipient', 'subject', 'created_at', 'get_previous_message','get_reply')
    search_fields = ('subject', 'content', 'sender__username', 'recipient__username','get_previous_message', 'get_reply')
    ordering = ('-created_at',)
    def get_previous_message(self, obj):
        """Displays the previous message in a human-readable format."""
        return obj.previous_message.subject if obj.previous_message else "None"
    get_previous_message.subject = "Previous Message"

    def get_reply(self, obj):
        """Displays the reply message in a human-readable format."""
        return obj.reply.subject if obj.reply else "None"
    get_reply.subject = "Reply Message"

# Registers the TutorLangRequest model with custom admin configuration (with filtering and search fields).
@admin.register(TutorLangRequest)
class TutorLangRequest(admin.ModelAdmin):
    list_display = ('tutor', 'language', 'action')
    list_filter = ('tutor', 'action', 'language', 'current_language', 'requested_language')
    search_fields = ('tutor__user__username', 'language__name', 'current_language__name', 'requested_language__name')

# Register the TutorAvailability model with custom admin configuration (with filtering and search fields).
@admin.register(TutorAvailability)
class TutorAvailability(admin.ModelAdmin):
    list_display = ('tutor', 'day', 'start_time', 'end_time', 'action', 'availability_status')
    list_filter = ('tutor', 'action', 'availability_status', )
    search_fields = ('tutor__UserID__username', 'day', 'availability_status')