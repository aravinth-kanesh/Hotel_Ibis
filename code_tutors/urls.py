"""
URL configuration for code_tutors project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from tutorials import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('log_in/', views.LogInView.as_view(), name='log_in'),
    path('log_out/', views.log_out, name='log_out'),
    path('password/', views.PasswordView.as_view(), name='password'),
    path('profile/', views.ProfileUpdateView.as_view(), name='profile'),
    path('sign_up/', views.SignUpView.as_view(), name='sign_up'),
    # student request form
    path('request/create/', views.StudentRequestCreateView.as_view(), name='create_request'),
    path('request/view/', views.StudentRequestListView.as_view(), name='view_request'),


    # messages
    path('message/send/', views.SendMessageView.as_view(), name='send_message'),
    path('message/send/<int:reply_id>/', views.SendMessageView.as_view(), name='reply_message'),
    path('messages/', views.AllMessagesView.as_view(), name='all_messages'),
    path('messages/<int:pk>/', views.MessageDetailView.as_view(), name='message_detail'),

    path('invoice/<int:invoice_id>/approve/', views.approve_invoice, name='approve_invoice'),

    #dashboard tools (admin)
    path('user/<int:user_id>/delete/', views.delete_user, name='delete_user'),
    path('user/<int:user_id>/update-role/', views.update_user_role, name='update_user_role'),

    path('calendar/', views.calendar_view, name='calendar'),
    path('calendar/<int:year>/<int:month>/', views.calendar_view, name='calendar'),
    path('lessons/<int:year>/<int:month>/<int:day>/', views.lessons_on_day, name='lessons_on_day'),
    path('tutor/calendar/', views.tutor_calendar_view, name='tutor_calendar'),
    path('tutor/calendar/<int:year>/<int:month>/', views.tutor_calendar_view, name='tutor_calendar'),
    path('tutor/lessons/<int:year>/<int:month>/<int:day>/', views.lessons_on_day_tutor, name='lessons_on_day_tutor'),
    # Admin URLs
    path('students/', views.student_list, name='student_list'),
    path('invoices/create/<int:student_id>/', views.create_invoice, name='create_invoice'),
    path('view/<int:student_id>/invoices/', views.student_invoices_admin, name='student_invoices_admin'),
    path('set-price/<int:student_id>/', views.set_price, name='set_price'),
    
    # Invoice URLs
    path('invoices/<int:invoice_id>/', views.invoice_detail, name='invoice_detail'),
    path('invoices/pay/<int:invoice_id>/', views.pay_invoice, name='pay_invoice'),

    # Student Invoice List
    path('my-invoices/', views.student_invoices, name='student_invoices'),

    path('process-request/<int:request_id>/', views.StudentRequestProcessingView.as_view(), name='process_request'),
    path('lesson-update/<int:lesson_id>/', views.LessonUpdateView.as_view(), name='lesson_update'),
    # tutor pages
    path('manage-languages/', views.manage_languages, name='manage_languages'),
    path('tutor/manage-availability/', views.TutorAvailabilityView.as_view(), name='tutor_availability_request'),
    path('tutor/manage-availability/<int:availability_id>/edit', views.TutorAvailabilityView.as_view(), name='edit_tutor_availability'),
    path('tutor/manage-availability/<int:availability_id>/delete', views.TutorAvailabilityView.as_view(), name='delete_tutor_availability'),

]
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)