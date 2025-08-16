from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('summary/<uuid:transcript_id>/', views.summary_view, name='summary_view'),
    path('summary/update/<uuid:transcript_id>/', views.update_summary, name='update_summary'),
    path('summary/share/<uuid:transcript_id>/', views.share_summary, name='share_summary'),
]