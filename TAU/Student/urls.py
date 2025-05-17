
from django.urls import path
from . import views
# from django.urls import path


urlpatterns = [
    
    path('register/',views.register_view, name='register'),              

    path('',views.lp, name='loginn'),   
    path('logout/',views.logout, name='logout'),
    path('accounts/login/', views.lp), 
    
    
    path('newticket/',views.nt, name='nt'), # for student dashboard
    path('landingpage/',views.landingpage, name='landingpage'), # for student dashboard

]