from django.urls import path
from shop import views

app_name = 'shop'

urlpatterns = [
    path('course/<int:course_id>/', views.course_detail, name='course_detail'),
    path('', views.index, name='index'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='user_login'),
    path('logout/', views.user_logout, name='user_logout'),
    path('courses/', views.courses, name='courses'),
    path('upload/', views.upload_course, name='upload_course'),
    path('cart/', views.cart, name='cart'),
    path('add-to-cart/<int:course_id>/', views.add_to_cart, name='add_to_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('ref/<str:code>/', views.affiliate_redirect, name='affiliate_redirect'),
    path('purchases/', views.purchases, name='purchases'),
    path('affiliate/', views.affiliate_dashboard, name='affiliate_dashboard'),
    path('affiliate/<str:code>/', views.affiliate_redirect, name='affiliate_redirect'),
    path('instructor/', views.instructor_dashboard, name='instructor_dashboard'),
    path('course/<int:course_id>/', views.course_detail, name='course_detail'),
    path('lesson/<int:lesson_id>/', views.lesson_detail, name='lesson_detail'),
    path('lesson/<int:lesson_id>/upload-resource/', views.upload_resource, name='upload_resource'),
]