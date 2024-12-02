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

]
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)