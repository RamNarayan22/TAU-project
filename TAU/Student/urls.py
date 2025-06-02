from django.urls import path
from . import views
# from django.urls import path

app_name = 'student'

urlpatterns = [
    # Root URL should check user type and redirect accordingly
    path('', views.student_root, name='root'),
    
    # Authentication URLs
    path('login/', views.lp, name='loginn'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('accounts/login/', views.lp),
    
    # Student dashboard URLs
    path('newticket/', views.nt, name='nt'), # for student dashboard
    path('landingpage/', views.landingpage, name='landingpage'), # for student dashboard

]