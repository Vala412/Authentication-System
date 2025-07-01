from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.LoginView.as_view(), name='login'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('activate/<str:activation_code>/', views.ActivateView.as_view(), name='activate'),
    path('resend-activation/', views.ResendActivationView.as_view(), name='resend_activation'),
    path('profile/', views.profile_view, name='profile'),
]