"""
URL configuration for djangoproject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
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
from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from djangoApp import views
from djangoApp import views_author
from djangoApp import views_more

urlpatterns = [
    path('admin/', admin.site.urls),
        path('', views.home, name='home'),
    path('story/<int:story_id>/', views.story_detail, name='story_detail'),
    

    path('play/<int:story_id>/', views.play_story, name='play_story'),
    path('play/<int:story_id>/page/<int:page_id>/', views.play_page, name='play_page'),
 
    path('statistics/', views.stats, name='statistics'),
    path('register/', views_author.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),

    path('my-stories/', views_author.my_stories, name='my_stories'),
    path('my-history/', views_more.my_history, name='my_history'),

    path('create-story/', views_author.create_story, name='create_story'),
    path('edit-story/<int:story_id>/', views_author.edit_story, name='edit_story'),
    path('delete-story/<int:story_id>/', views_author.delete_story, name='delete_story'),
    

    path('create-page/<int:story_id>/', views_author.create_page, name='create_page'),
    path('edit-page/<int:page_id>/', views_author.edit_page, name='edit_page'),
    path('delete-page/<int:page_id>/', views_author.delete_page, name='delete_page'),

    path('create-choice/<int:page_id>/', views_author.create_choice, name='create_choice'),
    path('delete-choice/<int:choice_id>/', views_author.delete_choice, name='delete_choice'),

    path('suspend-story/<int:story_id>/', views_author.suspend_story, name='suspend_story'),
    path('unsuspend-story/<int:story_id>/', views_author.unsuspend_story, name='unsuspend_story'), 

    path('story-tree/<int:story_id>/', views_author.story_tree, name='story_tree'),
 
]
