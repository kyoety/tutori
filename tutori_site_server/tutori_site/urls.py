"""tutori_site URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
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
from django.urls import path, include
from tutori import views
from django.conf.urls import include, url
from . import settings
from django.contrib.staticfiles.urls import static, staticfiles_urlpatterns
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),


    url(r'^$', views.index, name="index"),
    #panel controls
    
    path('sendComments', views.sendComments, name = 'sendComments'),

    path('mainPanel', views.mainPanel, name = 'mainPanel'),
    path('saveProfile', views.saveProfile, name = 'saveProfile'),
    
    #path('profile', views.profile, name = 'profile'),
    #path('editProfile',views.editProfile, name = 'editProfile'),
    #path('editStudentProfile', views.editStudentProfile, name = 'editStudentProfile'),

    #search controls
    path('subjects', views.subjects, name = 'subjects'),
    path('oneSubject', views.oneSubject, name = 'oneSubject'),
    path('loadTutorInfo',views.loadTutorInfo, name = 'loadTutorInfo'),
    path('submitEventRequest',views.submitEventRequest, name = 'submitEventRequest'),
    path('acceptSlots',views.acceptSlots, name = 'acceptSlots'),  
    path('cancelSlots',views.cancelSlots, name = 'cancelSlots'),  

    path('afterLogin',views.afterLogin, name = 'afterLogin'),
    path('activateAccount',views.activateAccount, name = 'activateAccount'),
    
 #   path('tutor-1', views.tutor1, name = 'tutor-1'),
    path('tutor-2', views.tutor2, name = 'tutor-2'),
    
    path('messageUser',views.messageUser, name = 'messageUser'),  
    path('sendMessage',views.sendMessage, name = 'sendMessage'),  
    path('getMessages',views.getMessages, name = 'getMessages'),  
    path('conversations',views.conversations, name = 'conversations'),  
    path('archiveConv',views.archiveConv, name = 'archiveConv'),  

    path('getCalendarContetData',views.getCalendarContetData, name = 'getCalendarContetData'),  
    path('setMySchedule',views.setMySchedule, name = 'setMySchedule'),    
   
    path('viewEventWithId',views.viewEventWithId, name = 'viewEventWithId'),  


    path('terms',views.terms, name = 'terms'),  


    path('stayaway/IXio9sK/showAdm',views.showAdmiPage, name = 'IOPIP'),  

    path('stayaway/IXio9sK/showRoomMembers',views.showRoomMembers, name = 'IOPIP'),  
    path('stayaway/IXio9sK/showTutors',views.showTutors, name = 'IOPIP'),  
    
    #path('stayaway/IXio9sK/invitePeople',views.invitePeople, name = 'IOPIP'),  
    path('stayaway/IXio9sK/enableAdmin',views.enableAdmin, name = 'IOPIP'),  
    path('stayaway/IXio9sK/approveStudent',views.approveStudent, name = 'IOPIP'),  
    path('stayaway/IXio9sK/uploadTutorCsv',views.uploadTutorCsv, name = 'IOPIP'),  
    path('stayaway/IXio9sK/removePeople',views.removePeople, name = 'IOPIP'),  

]
"""   path('importfile', views.importfile, name = 'importfile') 
    path('science', views.science, name = 'science'),
    path('math', views.math, name = 'math'),
"""
urlpatterns += staticfiles_urlpatterns()
urlpatterns += static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)