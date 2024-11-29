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
from django.http import HttpResponse

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('log_in/', views.LogInView.as_view(), name='log_in'),
    path('log_out/', views.log_out, name='log_out'),
    path('password/', views.PasswordView.as_view(), name='password'),
    path('profile/', views.ProfileUpdateView.as_view(), name='profile'),
    path('sign_up/', views.SignUpView.as_view(), name='sign_up'),
    path('request/create/', views.StudentRequestCreateView.as_view(), name='create_request'),
    path('test/', lambda request: HttpResponse("Test page")),
    path('calendar/', views.calendar_view, name='calendar'),
    path('calendar/<int:year>/<int:month>/', views.calendar_view, name='calendar'),
    path('lessons/<int:year>/<int:month>/<int:day>/', views.lessons_on_day, name='lessons_on_day'),
    path('tutor/calendar/', views.tutor_calendar_view, name='tutor_calendar'),
    path('tutor/calendar/<int:year>/<int:month>/', views.tutor_calendar_view, name='tutor_calendar'),
    path('tutor/lessons/<int:year>/<int:month>/<int:day>/', views.lessons_on_day_tutor, name='lessons_on_day_tutor'),
    # Admin URLs
    path('students/', views.student_list, name='student_list'),
    path('invoices/create/<int:student_id>/', views.create_invoice, name='create_invoice'),
    path('admin/students/<int:student_id>/invoices/', views.student_invoices_admin, name='student_invoices_admin'),
    # Invoice URLs
    path('invoices/<int:invoice_id>/', views.invoice_detail, name='invoice_detail'),
    path('invoices/pay/<int:invoice_id>/', views.pay_invoice, name='pay_invoice'),

    # Student Invoice List
    path('my-invoices/', views.student_invoices, name='student_invoices'),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)