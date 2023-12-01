from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.db.models import Q
from .models import  Tutori_admin, Tutori_invited_list, Tutoriacc_user, Tutoriacc_tutor, Tutoriacc_conversations,Tutoriacc_conversations_user, Tutoriacc_messages, Tutoriacc_Event, Tutoriacc_TutorSlots
from datetime import datetime, timedelta, date, time, timedelta
#from .utility import Calendar
#from django.utils.safestring import mark_safe
#from django.views.generic import ListView
import calendar
from django.shortcuts import redirect
from django.core.exceptions import ObjectDoesNotExist
from django.core import serializers
import json

from django.db import IntegrityError
import hashlib
import csv
import string
import random
from django.core.mail import send_mail,EmailMultiAlternatives
import threading
#from icalendar import Calendar as ICalendar, Event as ICalEvent

#import uuid

from django.conf import settings
from django.utils import timezone
import codecs

import os

SUBJECT_NUM = 22

## Panel Function


week_days = {1:'SUN',
            2:'MON', 
            3:'TUE', 
            4:'WED', 
            5:'THU', 
            6:'FRI', 
            7:'SAT', 
            }
SLOT_DURATION = 30


day_time_slots=["07:00","07:30","08:00","08:30","09:00","09:30","10:00",\
    "10:30","11:00","11:30","12:00","12:30","13:00","13:30","14:00","14:30","15:00",\
        "15:30","16:00","16:30","17:00","17:30","18:00","18:30","19:00","19:30","20:00",\
            "20:30","21:00","21:30","22:30","22:30"]
            
def mainPanel(request):
    
    tab =  request.GET.get('tab')

    my_dictionary = {}

    if  isAuthentcated(request):

        my_dictionary = populateProfileData(request)

        if "tutor" in my_dictionary:
            tutorSlots = Tutoriacc_TutorSlots.objects.filter(slot_tutor = my_dictionary["tutor"])
            slot_list =[]
            for   tutorSlot in tutorSlots :
                print("there is slot!")
                slot_list.append([tutorSlot.weekday,tutorSlot.start_time.strftime('%H:%M'),tutorSlot.end_time.strftime('%H:%M')])
            my_dictionary.update({"tutorslots" : slot_list})

            my_dictionary.update({"week_days":week_days})
            my_dictionary.update({"day_time_slots":day_time_slots})
        
        my_dictionary = populateSessionData(my_dictionary, request)

        if tab:
            my_dictionary.update({"tab":tab})
        return render(request, 'mainPanel.html', my_dictionary)

    else:
        return HttpResponseRedirect('/?errorlogin=1') # Redirect to home

def populateProfileData(request):
    my_dictionary = {}
    try:
        tu_user = Tutoriacc_user.objects.get(acc_user = request.user)
        my_dictionary = {"tu_user" : tu_user}
        my_dictionary.update({"isUser" : "true"})

        print(str(tu_user.acc_firstname))

        try:
            tutor =  Tutoriacc_tutor.objects.get(tu_user = tu_user)   
            my_dictionary.update({"tutor":tutor})
            #print(str(tutor))

            course_display_dict = createSubjectProfileDisplay(tutor.acc_subjects,"Grade ")
            my_dictionary.update({"course_dict": course_display_dict})       
                    
        except Tutoriacc_tutor.DoesNotExist:
            print("")

    except Tutoriacc_user.DoesNotExist:
        print("")
    return my_dictionary

def populateSessionData(my_dictionary, request):

    start_time = datetime.today() - timedelta(days=1)

    if "tutor" in my_dictionary:
        events_db = Tutoriacc_Event.objects.filter(evn_tutor = my_dictionary["tutor"], start_time__gte=start_time ).exclude(evn_status_str="Rejected")
    else:
        events_db = Tutoriacc_Event.objects.filter(evn_tutee = my_dictionary["tu_user"], start_time__gte=start_time )
    events = []

    for event in events_db:
        event_data=[event, event.start_time.strftime('%a %m/%d/%Y'), event.start_time.strftime('%H:%M'),event.end_time.strftime('%H:%M')  ]
        events.append (event_data)

    if (2-len(events)%2) >0:
        events.append(None)
    my_dictionary.update({"events":events})

    return my_dictionary


def getCalendarContetData(request):
    my_dictionary={}

    month = request.GET.get('month', None)

    if  isAuthentcated(request):
        my_dictionary = populateProfileData(request)

        my_dictionary = populateSessionData(my_dictionary, request)
        events = my_dictionary["events"]

        event_dict ={}
        for event in events:
            if event:
                if event[0].evn_status_str == "Accepted":
                    event_date = datetime.strptime(event[1], '%a %m/%d/%Y').date()
                    if event_date in event_dict:
                        event_dict[event_date].append((event[0],event[2],event[3]))
                    else:
                        event_dict.update({event_date:[(event[0],event[2],event[3])]})
    
        # use today's date for the calendar
        weeks = get_days_for_month_year(month)
        d = get_date(month)
        response_str = d.strftime("%b, %Y")+"^"+prev_month(d)+"^"+next_month(d)
        if month:
            cur_year, cur_month = (int(x) for x in month.split('-'))
        else:
            cur_year = datetime.today().year
            cur_month = datetime.today().month


        for days in weeks:
            weekday = 0
            for day in days:
                weekday= weekday+1
                response_str=response_str+"^"
                if day!= 0:
                    response_str=response_str+str(day)
                    curdate = date(cur_year, cur_month, day)

                    if curdate in event_dict:

                        response_str=response_str+"|"
                        for event_data in event_dict[curdate]:
                            other_guy = event_data[0].evn_tutor.tu_user

                            if(other_guy.acc_user ==  request.user):
                                other_guy = event_data[0].evn_tutee
                            response_str=response_str+"_"+str(event_data[0].id)+"-"+event_data[0].evn_subject+"-"+other_guy.acc_firstname+" "+ other_guy.acc_lastname
        
        print(response_str)
        return HttpResponse(response_str)

    else:
        return HttpResponse('NO PERMISSION')

def viewEventWithId(request):

    if  isAuthentcated(request):
        event_id = request.GET.get("ev_id")

        if len(event_id) >0:
            try:

                event = Tutoriacc_Event.objects.get(id=int(event_id))

                print("event user:("+str(event.evn_tutee.acc_user )+","+ str(event.evn_tutor.tu_user.acc_user) +") signed in User:"+str(request.user))
                if event.evn_tutee.acc_user == request.user:
                    other_user = event.evn_tutor.tu_user
                elif event.evn_tutor.tu_user.acc_user == request.user:
                    other_user = event.evn_tutee
                else:
                    return HttpResponse("NO OWNER PERMISSION")

                resp_str=event.evn_subject+"^With "+other_user.acc_firstname+" "+other_user.acc_lastname\
                    +"^"+event.start_time.strftime('%H:%M')+" - "+event.end_time.strftime('%H:%M')\
                        +"^"+event.evn_status_str\
                            +"^"+event.evn_description\
                                +"^"+event.evn_net_meeting\
                                    +"^"+str(other_user.acc_user.id)
                print(resp_str)

                return HttpResponse(resp_str)

            except Tutoriacc_Event.DoesNotExist:
                return HttpResponse("ERROR")
        else:
            return HttpResponse("ERROR")

    else:
        return HttpResponse('NO PERMISSION')

def setMySchedule(request): #used, tutor only
    
    if  isAuthentcated(request):
        for key, value in request.POST.items():
            print('Key: %s' % (key) ) 
            # print(f'Key: {key}') in Python >= 3.7
            print('Value %s' % (value) )
            # print(f'Value: {value}') in Python >= 3.7
            try:
                tutor = Tutoriacc_tutor.objects.get(tu_user__acc_user = request.user)

                fields_list =[['formCheck-1','start_time1','end_time1'],
                        ['formCheck-2','start_time2','end_time2'],
                        ['formCheck-3','start_time3','end_time3'],
                        ['formCheck-4','start_time4','end_time4'],
                        ['formCheck-5','start_time5','end_time5'],
                        ['formCheck-6','start_time6','end_time6'],
                        ['formCheck-7','start_time7','end_time7'],
                    ]
                
                Tutoriacc_TutorSlots.objects.filter(slot_tutor = tutor).delete()

                weekday = 1
                for fields in fields_list:
                    weekday_flag = request.POST.get(fields[0])
                    print(fields[0]+str(weekday_flag))

                    if weekday_flag:
                        start_time = get_time_day(request.POST.get(fields[1]))
                        end_time = get_time_day(request.POST.get(fields[2]))

                        tutor_slot= Tutoriacc_TutorSlots()
                        tutor_slot.start_time = start_time
                        tutor_slot.end_time = end_time
                        tutor_slot.slot_tutor = tutor
                        tutor_slot.weekday = weekday
                        tutor_slot.save()
                        print("save one slot")

                    weekday = weekday +1

                return HttpResponse('SUCCESS')

            except Tutoriacc_tutor.DoesNotExist:
                print("something wrong12")
 
                return HttpResponse('NO PERMISSION')

    else:
        return HttpResponse('NO PERMISSION')


def saveProfile(request):
    if  request.user.is_authenticated:

        try:
            user = Tutoriacc_user.objects.get(acc_user = request.user)
        except Tutoriacc_user.DoesNotExist:
            user = Tutoriacc_user()                
            user.acc_user = request.user
        user.acc_avatar = request.user.socialaccount_set.all()[0].get_avatar_url()
        user.acc_firstname = request.POST.get('firstname')
        user.acc_lastname = request.POST.get('lastname')
        user.acc_aboutme = request.POST.get('aboutme')
        user.acc_grade = request.POST.get('grade')
        if request.POST.get('homeschool'):
            user.homeschool = request.POST.get('homeschool')

        user.save()

        # is_tutor = request.POST.get('isTutor')

        # if is_tutor and is_tutor == '1': # saving for tutor

        #     try:
        #         tutor = Tutoriacc_tutor.objects.get(tu_user = user)

        #     except Tutoriacc_tutor.DoesNotExist:
        #         print("edit profile with new tutor user. shall not be here!!")
        #         #new user
        #         tutor = Tutoriacc_tutor()   
        #         tutor.tu_user = user
        #         tutor.save()


        #     # tutor.acc_subjects =""
        #     # subject_count = 1
        #     # while subject_count <= SUBJECT_NUM: 
        #     #     if request.POST.get('Subject'+str(subject_count)):
        #     #         subject_str = request.POST.get('Subject'+str(subject_count))
        #     #         tutor.acc_subjects = tutor.acc_subjects+"|"+ subject_str

        #     #     subject_count = subject_count +1    
        #     # print("subjects:"+tutor.acc_subjects )

        #     return HttpResponse('SUCCESS')
        # else:
        return HttpResponse('SUCCESS')
    else:
        return HttpResponse('NO PERMISSION')

# 
#
## Admin Functions##############
def showAdmiPage (request):
    my_dictionary = {}

    if  isAuthentcated(request):
            updateDictionaryWithUserInfo(request,my_dictionary)

    if isAdminAuthentcated(request):

            return render(request, 'admin_func.html', my_dictionary)
    else:
        return HttpResponseRedirect('/?error=login') # Redirect to home


def showTutors(request):
    # load a page with members of a room

    response_str=''

    if isAdminAuthentcated(request):

        tutor_list = ""
        pending_tutor_list=""
        requested_tutor_list=""
        expired_invites=""

        # invites only for tutors
        invites = Tutori_invited_list.objects.all()

        for invitation in invites:

            new_invitee = "^"+invitation.gmail_setting+"|"+str(invitation.invite_time.year)+"-"+str(invitation.invite_time.month)+"-"+str(invitation.invite_time.day)

            valid_date = invitation.invite_time + timedelta(days=(invitation.valid_days+1))

            CurrentDate = timezone.now()

            if CurrentDate > valid_date: #expired
                expired_invites = expired_invites+new_invitee
                #invitation.delete()
            #elif invitation.is_tutor:
            else: # shall be none
                pending_tutor_list= pending_tutor_list + new_invitee

                #print ("there are to be activated tutee. should not exist!!")
                #ending_tutee_list=pending_tutee_list + new_invitee


        students = Tutoriacc_tutor.objects.all()

        for student in students:

            if student.tu_user.acc_user == request.user:
                new_mem = "^"+student.tu_user.acc_firstname+" "+student.tu_user.acc_lastname+"|-1"
            else:
                new_mem = "^"+student.tu_user.acc_firstname+" "+student.tu_user.acc_lastname+"|"+str(student.tu_user.acc_user_id)+"|"+str(student.tu_user.homeschool)+"|"+str(student.tu_user.acc_grade)
            
            tutor_list = tutor_list + new_mem

        response_str = tutor_list+"~"+pending_tutor_list

        print("response_str="+response_str)

        return HttpResponse (response_str)                       
    else:
        return HttpResponse('NO PERMISSION')

def showRoomMembers(request):
    # load a page with members of a room

    response_str=''

    if isAdminAuthentcated(request):

        admin_list = ""
        tutee_list = ""
        pending_tutee_list=""


        students = Tutoriacc_user.objects.all()

        for student in students:

            if student.acc_user == request.user:
                new_mem = "^"+student.acc_firstname+" "+student.acc_lastname+"|-1"
            else:
                new_mem = "^"+student.acc_firstname+" "+student.acc_lastname+"|"+str(student.acc_user_id)+"|"+str(student.homeschool)+"|"+str(student.acc_grade)
            
            if student.is_approved:
                tutee_list = tutee_list + new_mem
            else:
                pending_tutee_list = pending_tutee_list+new_mem

        admins = Tutori_admin.objects.all()

        for admin in admins:
            admin_list = admin_list+"^"+admin.admin_user.first_name+" "+admin.admin_user.last_name

            if admin.admin_user == request.user:
                admin_list = admin_list +"|-1"

            else:
                admin_list = admin_list +"|"+str(admin.admin_user_id)

        response_str = admin_list+"~"+tutee_list+"~"+pending_tutee_list

        print("response_str="+response_str)

        return HttpResponse (response_str)                       
    else:
        return HttpResponse('NO PERMISSION')


def enableAdmin(request): #

    if isAdminAuthentcated(request):

        if request.method == 'POST':
            emails =  request.POST.get('ema')
            try:
                base_user = Tutoriacc_user.objects.get(acc_user__email = emails)
                print ("find the user")

                admin = Tutori_admin()
                admin.admin_user = base_user.acc_user
                admin.save()
                print ("enable the admin")

            except Tutoriacc_user.DoesNotExist:
                print ("something wrong, cannot delete the user")
                return HttpResponse('NO ACCOUNT')

            except IntegrityError:
                print ("already a admin")
                return HttpResponse('ALREADY')

            return HttpResponse('SUCCESS')

    else:
        return HttpResponse('NO PERMISSION')


def approveStudent(request):
    user_id = request.POST.get('uid')

    if isAdminAuthentcated(request):
        
        if user_id and len(user_id)>0:
            try:
                tu_user = Tutoriacc_user.objects.get(acc_user_id = user_id)
                tu_user.is_approved = True
                tu_user.save()
            except Tutoriacc_user.DoesNotExist:
                print ("something wrong, cannot delete the user")

        return HttpResponse('SUCCESS')

    else:
        return HttpResponse('NO PERMISSION')


##load new requests from CSV from google form
def uploadTutorCsv(request):

    if isAdminAuthentcated(request):

        if request.method == 'POST':
            csv_file =  request.FILES['csv_file']  # here you get the files needed

            if not csv_file.name.endswith('.csv'):
                
                return  HttpResponse('NO CSV')
            
            csv_file.seek(0, os.SEEK_END)

            print("file size =" + str(csv_file.tell()))
                
            # If file is too large
            if csv_file.multiple_chunks():
                return HttpResponse('File is too big (' + str(csv_file.size(1000*1000))+' MB)')

            # get the path of the file saved in the server
            #csv_file_txt =  TextIOWrapper(csv_file.file, encoding="utf-8")  # here you get the files needed

            #for line in csv_file:
             #       print(line)

            #for line in csv_file_txt:
              #      print(line)
            load_new_aapproved_tutor_from_csv(csv_file,request)
            
            return HttpResponse('SUCCESS')

    else:
        return HttpResponse('NO PERMISSION')

    
def load_new_aapproved_tutor_from_csv(csv_file, request):
    # do try catch accordingly
    # open csv file, read lines


    students = csv.DictReader(codecs.iterdecode(csv_file, 'utf-8')) 

    for new_student_details in students:
        print(str(new_student_details) )


        # create a dictionary of student details

        req_email = new_student_details['Email']
        print("email:"+ req_email)
        try:
            tutor = Tutoriacc_tutor.objects.get(tu_user__acc_user__email = req_email)
            #already exit, skip
        except Tutoriacc_tutor.DoesNotExist:
            try:
                invites = Tutori_invited_list.objects.get(gmail_setting = req_email)
                invites.delete()
                #already exit, skip
            except Tutori_invited_list.DoesNotExist:
                #new request start to process
                pass
            invite = Tutori_invited_list()
            invite.admin = request.user.email
            invite.firstname = new_student_details['First Name']
            invite.lastname  = new_student_details['Last Name']
            invite.gmail_setting = new_student_details['Email']
            invite.aboutme = new_student_details['Is there anything else you would like us to know? (Optional)']
            invite.homeschool = new_student_details['What is the name of the school you currently attend?']

            grade_info = new_student_details['What grade are you in?'] 
            if grade_info == "Post Secondary":
                invite.grade = 13
            else:
                invite.grade = int(grade_info )
            
            # need to translate subject feld
            
            subject_question_map = [('Science', 'What subject(s) will you be tutoring? [Science]'),
                                    ('Math', 'What subject(s) will you be tutoring? [Math]'),
                                    ('Physics', 'What subject(s) will you be tutoring? [Physics]'),
                                    ('Biology', 'What subject(s) will you be tutoring? [Biology]'),
                                    ('Chemistry', 'What subject(s) will you be tutoring? [Chemistry]'),
                                    ('Calculus', 'What subject(s) will you be tutoring? [Calculus]'),
                                    ('Statistics', 'What subject(s) will you be tutoring? [Statistics]'),
                                    ('French', 'What subject(s) will you be tutoring? [French]'),
                                    ('English', 'What subject(s) will you be tutoring? [English]'),
                                    ]
            subject_field=""
            for (subject,question) in subject_question_map:
                grade_data = new_student_details[question]
                if len(grade_data) >0:
                    grade_list = grade_data.split(';')
                    for grade_info in grade_list:
                        subject_field = subject_field+"|"+subject+":"+grade_info
                    subject_field 

            invite.subjects=subject_field

            one_time_code = OTP_generator()
            print(invite.gmail_setting+ "'s OTP="+one_time_code)
            hashed_code = hashlib.sha256(one_time_code.encode('utf-8')).hexdigest()
            invite.one_time_activation_code = hashed_code 
            invite.save()

        # send email

            subject = 'Your application to be a tutor for Tutori.me is approved'
            message = ' Hi, there, \n\n Congradulations and welcome to Tutori team! Your tutor application to Tutori as a peer tutor has been  approved' \
                + ' \n\n Please go to https://www.tutori.me and use one time activation code ['+one_time_code+'] to complete your registration and activate your tutor account. '  \
                + ' \n Please contact us if you run into any issues. \n\n \n\From the Tutori Team.'

            email_from = settings.EMAIL_HOST_USER
            recipient_list = [invite.gmail_setting,]
            
            t1 = threading.Thread(target=send_mail, args=[subject, message, email_from, recipient_list])
            t1.start()
                            # for the foreign key field current_class in Student you should get the object first and reassign the value to the key

    csv_file.close()

# def invitePeople(request):
    
#     is_tutor = request.POST.get('isT')
#     is_ind_list = request.POST.get('isInd')

#     if isAdminAuthentcated(request):

#             if request.method == 'POST':
#                 emails =  request.POST.get('ema')

#                 if is_tutor == "1":
#                     inviteAMem(emails, True, request.user.email)

#                 elif is_ind_list == "1": #list of individual emails
#                     email_list = emails.split(',')

#                     for one_email in email_list:
#                         print("invite to:"+one_email)
#                         inviteAMem(one_email, False, request.user.email)
#                 else:
#                     counts =  request.POST.get('num')

#                     recieving_email =  request.POST.get('rvema')
#                     inviteAGroup(emails, recieving_email, request.user.email, counts)

#                 return HttpResponse('SUCCESS')

#     else:
#         return HttpResponse('NO PERMISSION')

# def inviteAMem(email, is_Tutor, admin):

#     Tutori_invited_list.objects.filter(gmail_setting = email).delete()

#     invitation = Tutori_invited_list()
#     invitation.gmail_setting = email
#     invitation.is_tutor = is_Tutor 
#     invitation.invitation_recievor = email
#     one_time_code = OTP_generator()
#     print(invitation.gmail_setting+ "'s OTP="+one_time_code)
#     hashed_code = hashlib.sha256(one_time_code.encode('utf-8')).hexdigest()
#     invitation.one_time_activation_code = hashed_code 
#     invitation.admin = admin
#     invitation.activation_code_use_count = -1
#     invitation.save()

#     # send email
#     role_string = "as a student"
#     if is_Tutor:
#         role_string = "as a tutor"
#     subject = 'You are invited to join Tutori Program.'
#     message = ' Hi, there, \n\n You are invited to join the Tutori program '+ role_string\
#         + ' \n\n Please go to https://www.tutori.me and using one time activation code ['+one_time_code+'] to complete your registration: '  \
#         + ' \n Please contact us if you run into any issues. \n\nThanks From Tutori Team.'

#     email_from = settings.EMAIL_HOST_USER
#     recipient_list = [invitation.gmail_setting,]
    
#     t1 = threading.Thread(target=send_mail, args=[subject, message, email_from, recipient_list])
#     t1.start()


def OTP_generator(size=6):

    chars=string.ascii_uppercase + string.digits

    return ''.join(random.choice(chars) for _ in range(size))


#def approveTutor(request): #??? approve in excel sheet
    # user_id = request.POST.get('uid')

    # if isAdminAuthentcated(request):
        
    #     if user_id and len(user_id)>0:
    #         try:
    #             tu_user = Tutoriacc_user.objects.get(acc_user_id = user_id)
    #             tu_user.is_approved = True
    #             tu_user.save()
    #         except Tutoriacc_user.DoesNotExist:
    #             print ("something wrong, cannot delete the user")

    #     return HttpResponse('SUCCESS')

    # else:
    #     return HttpResponse('NO PERMISSION')

def removePeople(request):
    
    user_id = request.POST.get('uid')
    admin_id = request.POST.get('adminid')

    if isAdminAuthentcated(request):
        
        if user_id and len(user_id)>0:
            try:
                Tutoriacc_user.objects.get(acc_user_id = user_id).delete()
            except Tutoriacc_user.DoesNotExist:
                print ("something wrong, cannot delete the user")

        
        if admin_id and len(admin_id)>0 and admin_id != request.user :
            try:
                Tutori_admin.objects.get(admin_user_id = admin_id).delete()
            except Tutori_admin.DoesNotExist:
                print ("something wrong, cannot delete the admin")

        return HttpResponse('SUCCESS')

    else:
        return HttpResponse('NO PERMISSION')


##############################Normal Flows######################
def index(request):

    my_dictionary = {}

    if isAuthentcated(request):
        my_dictionary = populateProfileData(request )

    if request.user.is_authenticated:
        is_activate = request.GET.get('ACTA')
        if(is_activate == "1"): # for tutor
            my_dictionary.update({"is_activate" : "true"}) # read to be a tutor
        else:
            is_profile = request.GET.get('PRO')
            if(is_profile == "1"):
                my_dictionary.update({"is_profile" : "true"})
                #tu_user = Tutoriacc_user()
                #tu_user.acc_lastname = request.user.socialaccount_set.all()[0].extra_data['family_name']
                #tu_user.acc_firstname = request.user.socialaccount_set.all()[0].extra_data['given_name']
                #my_dictionary = {"tu_user" : tu_user}

                if 'family_name' in request.user.socialaccount_set.all()[0].extra_data:
                    my_dictionary.update({"social_lastname" : request.user.socialaccount_set.all()[0].extra_data['family_name'] })
                if 'given_name' in request.user.socialaccount_set.all()[0].extra_data:
                    my_dictionary.update({"social_firstname" : request.user.socialaccount_set.all()[0].extra_data['given_name']})

    return render(request, 'landing.html', my_dictionary)


def sendComments(request): 

    subject = 'User comments'
    message = 'Following are comments from User:\n\n' + \
              ' Last Name:' +request.POST.get('comment_lastname')+'\n\n' + \
              ' First Name:' +request.POST.get('comment_firstname')+ '\n\n' + \
              ' Email:' +request.POST.get('comment_email')+ '\n\n' + \
              ' Comments:'+request.POST.get('comment_message')

    email_from = settings.EMAIL_HOST_USER
    recipient_list = [settings.EMAIL_HOST_USER]
    
    t1 = threading.Thread(target=send_mail, args=[subject, message, email_from, recipient_list])
    t1.start()
    print("there is a comment submited")
    return  HttpResponse('SUCCESS')


def afterLogin(request):

    is_continue_as_normal = False
    try:
        invitation = Tutori_invited_list.objects.get(gmail_setting = request.user.email)

        valid_date = invitation.invite_time + timedelta(days=(invitation.valid_days+1))

        CurrentDate = timezone.now()

        if CurrentDate <=  valid_date:
            return HttpResponseRedirect('/?ACTA=1') # Pending activation must be activated
        else: #expired inivites as normal user
            is_continue_as_normal = True

    except Tutori_invited_list.DoesNotExist: #normal user
        is_continue_as_normal = True

    if  is_continue_as_normal:
        if  isAuthentcated(request):
            return HttpResponseRedirect('/mainPanel') # Redirect to home
        else:
            return HttpResponseRedirect('/?PRO=1') # New user Redirect to Profile
    


def activateAccount(request): # it will also be used to activate invite only account #in called by JavaScript

    if  request.user.is_authenticated:
            try:
                one_time_code = request.POST.get('activation_code')
                print("one_time_code:"+one_time_code)
                hashed_code = hashlib.sha256(one_time_code.encode('utf-8')).hexdigest()
                print ("hash code="+ hashed_code)
                invitation = Tutori_invited_list.objects.get(one_time_activation_code = hashed_code)

                is_invited = False

                valid_date = invitation.invite_time + timedelta(days=(invitation.valid_days+1))

                CurrentDate = timezone.now()

                if CurrentDate > valid_date:
                    #invitation.delete()
                    return HttpResponse('EXPIRED')

                if invitation.gmail_setting == request.user.email:
                    is_invited = True
                else:
                    return HttpResponse('NO INVITES')
                
    

                if is_invited:
                    try:
                        baseuser = Tutoriacc_user.objects.get(acc_user = request.user)
                    except Tutoriacc_user.DoesNotExist:
                        baseuser = Tutoriacc_user()
                        baseuser.acc_user = request.user
                    baseuser.acc_avatar = request.user.socialaccount_set.all()[0].get_avatar_url()
                    baseuser.acc_lastname = invitation.lastname
                    baseuser.acc_firstname = invitation.firstname
                    baseuser.acc_aboutme = invitation.aboutme
                    baseuser.acc_grade = invitation.grade
                    baseuser.homeschool = invitation.homeschool
                    baseuser.is_approved = True
                    baseuser.save()

                    #if invitation.is_tutor:
                    tutor = Tutoriacc_tutor()
                    tutor.tu_user = baseuser
                    tutor.acc_subjects = invitation.subjects
                    tutor.save()

                    invitation.delete() #clean up

                    return HttpResponse('SUCCESS')


            except Tutori_invited_list.DoesNotExist:
                return HttpResponse('NO INVITES')     
                #show alert and try it again
    else:
        return HttpResponse('NO PERMISSION')



def tutor2(request):
    my_dictionary={}

    if  isAuthentcated(request):
        updateDictionaryWithUserInfo(request,my_dictionary)

        return render(request, 'tutor-2.html',my_dictionary)

    else:
        return HttpResponseRedirect('/?errorlogin=1') # Redirect to home


def subjects(request):
    my_dictionary = {}

    if  isAuthentcated(request):
        updateDictionaryWithUserInfo(request,my_dictionary)
        return render(request, 'subjects.html', my_dictionary)
    else:
        return HttpResponseRedirect('/?errorlogin=1') # Redirect to home


sub_color = {'math':('5762d5','#5762d5' ),
            'calculus':('5762d5','#5762d5' ),
            'statistics':('5762d5','#5762d5' ),
             'science':('80ddd9','80ddd9' ), 
             'physics':('80ddd9','80ddd9' ), 
             'chemistry':('80ddd9','80ddd9' ), 
             'biology':('80ddd9','80ddd9' ), 
             'french':('f47a62','f47a62' ), 
             'humanities':('1ec161','1ec161' ), 
             'history':('1ec161','1ec161' ), 
             'economics':('1ec161','1ec161' ), 
             'geography':('1ec161','1ec161' ), 
             'sat':('9ca5ff','9ca5ff' ), 
             'english':('f7bc38','f7bc38' ) }


sub_supersets = {'math':['math','calculus','statistics','computer science' ], 
             'science':['science','physics','chemistry','biology'], 
             'humanities':['history','economics', 'geography' ], 
              }

def oneSubject(request): # not use basic template
    sub = request.GET.get('sub')
    if sub:
        sub = sub.lower()
    grade = request.GET.get('grade')

    filter_str = sub
    filter = None

    sub_display = sub
    grade_display = None
    if grade:
        grade_display = "Grade "+grade

    if sub in sub_supersets:
        sub_list = sub_supersets.get(sub)
        for sub_ext in sub_list:
            filter_str = sub_ext
            if grade:
                filter_str=filter_str+":"+grade
            if filter:
                filter = filter|(Q(acc_subjects__icontains=filter_str))
            else:
                filter = (Q(acc_subjects__icontains=filter_str))
    else:
        if grade:
            filter_str=filter_str+":"+grade
        filter = (Q(acc_subjects__icontains=filter_str))

        for super_sub, child_subs in sub_supersets.items():
            for child_sub in child_subs:
                if child_sub == sub and sub!= super_sub:
                    sub_display = super_sub
                    if grade_display:
                        grade_display = sub.capitalize()+" "+grade #display Bio 11 as grade
                    else:
                        grade_display = sub.capitalize()
                    break
            
            if sub_display == super_sub:
                break

    if  isAuthentcated(request):

        tutors = Tutoriacc_tutor.objects.filter(filter)

        tutor_list = []
        subject_txt = ""
        for tutor in tutors:
            subject_str = tutor.acc_subjects
            if subject_str:
                one_subject_strs= subject_str.split("|")
                for one_subject_str in one_subject_strs:
                    one_subject_title_strs= one_subject_str.split(":")
                    if(one_subject_title_strs[0] not in subject_txt):
                        if len(subject_txt) > 0:
                            subject_txt = subject_txt+","
                        subject_txt = subject_txt+one_subject_title_strs[0]

            tutor_data = [tutor,subject_txt]
            tutor_list.append(tutor_data)


        print ("tutor size =" + str(len(tutor_list)))

        remain_spot_one_row = 4 - len(tutor_list) % 4

        while remain_spot_one_row > 0:
            tutor_list.append(None)
            remain_spot_one_row = remain_spot_one_row -1

        primary_color,secondary_color = sub_color.get('science')

        if sub in sub_color:
            primary_color,secondary_color  = sub_color.get(sub)
        
        my_dict = {'tutors': tutor_list, 
                    "primary_color":primary_color,
                    "secondary_color" :secondary_color,
                    "subject_name":sub_display.capitalize(),}

        if grade_display:  
            my_dict.update ({"grade_num":grade_display,})          
                    
        updateDictionaryWithUserInfo(request,my_dict)

        return render(request, 'onesubject.html', context=my_dict)
    else:
        return HttpResponseRedirect('/?errorlogin=1') # Redirect to home


def loadTutorInfo(request):
    response=""

    if  isAuthentcated(request):

        tutor_id = request.GET.get('uid')
        print("id="+(tutor_id))

        try:
            tutor = Tutoriacc_tutor.objects.get(tu_user_id = tutor_id)

            response = tutor.tu_user.acc_firstname+ " " + tutor.tu_user.acc_lastname
            response = response +"^"+str(tutor.tu_user.acc_grade)
            response = response +"^"+tutor.tu_user.acc_aboutme


            course_display_dict = createSubjectProfileDisplay(tutor.acc_subjects,"")
            course_tutor_str ="" # not in use any more leave as empty
            course_tutor_selection_str =""

            for item in course_display_dict.items():
                #course_tutor_str = course_tutor_str+"#"+item[0]+" ( "+item[1]+" ) "
                course_tutor_selection_str = course_tutor_selection_str+"|"+item[0]+"_"+item[1]
            response = response +"^"+course_tutor_str

            tutor_slots = Tutoriacc_TutorSlots.objects.filter(slot_tutor = tutor)


            slots_str=""

            for slot in tutor_slots:

                start_time  = slot.start_time
                end_time = slot.end_time

                slots_str = slots_str +"|"+ week_days[slot.weekday] +" ("+  start_time.strftime('%H:%M')+" - "+end_time.strftime('%H:%M')+")"
            #    session_available
            #slots_str="| Monday ( 9pm- 10pm ) | Tuesday ( 8pm-11pm )  | Friday ( 8pm-11pm )"
            if len(slots_str) > 0:
                response = response +"^" +slots_str
            else:
                response = response +"^" +"No Slots Available"


            response = response +"^"+tutor.tu_user.acc_avatar

            booked_sessions = Tutoriacc_Event.objects.filter(evn_tutor =tutor, evn_status_str = "Accepted")

            available_slots = findSlotForWeekday(tutor_slots,booked_sessions)

            available_slots_str=""

            for slot in  available_slots:
                time_str=""
                available_slots_str = available_slots_str +"|"+ slot.strftime('%m/%d/%Y, %H:%M %a')

            response = response +"^" +available_slots_str
            response = response +"^" +course_tutor_selection_str
            response = response +"^" +tutor.tu_user.acc_firstname

            print(response)

            return HttpResponse(response)

        except Tutoriacc_tutor.DoesNotExist:
            print("no user for selected profile")
            return HttpResponse("ERROR")
    else:
        return HttpResponse("NO PERMISSION")


BOOK_WEEKS = 2

def findSlotForWeekday( slots, booked_events):


    time_slots=[]


    mins_added = timedelta(minutes = SLOT_DURATION)

    today = date.today()
    for k in range(0, BOOK_WEEKS):
        start_time = time(0,0,0)

        #    session_available
        for slot in slots:  
            next_weekday_date = today + timedelta( (slot.weekday + 5 - today.weekday()) % 7 +7*k) 


            if( slot.start_time < slot.end_time):
                start_time = slot.start_time
                end_time = slot.end_time
                tutor_booked_start_time = datetime.combine(next_weekday_date, time(start_time.hour, start_time.minute,start_time.second)) 
                tutor_booked_end_time = datetime.combine(next_weekday_date, time(end_time.hour, end_time.minute,end_time.second))  
                while (tutor_booked_start_time < tutor_booked_end_time):
                    # check if it is already booked
                    event_booked_at_time = booked_events.filter(start_time = tutor_booked_start_time)
                    if not event_booked_at_time:
                        time_slots.append(tutor_booked_start_time)
                    # no user create user first
                    tutor_booked_start_time = tutor_booked_start_time + mins_added
                    
                #tutor_booked_start_time = tutor_booked_start_time + mins_added
    
    time_slots.sort()

    return time_slots


def terms(request):

    my_dictionary={}

    if  isAuthentcated(request):
        updateDictionaryWithUserInfo(request,my_dictionary)

        return render(request, 'terms.html', my_dictionary)

    else:
        return HttpResponseRedirect('/?errorlogin=1') # Redirect to home

## Calendar views ???

def submitEventRequest( request): #updated used 

    if  request.user.is_authenticated:

        try:
            user = Tutoriacc_user.objects.get(acc_user = request.user)

            if user.is_approved:
              
                event_id = request.POST.get('event_id')

                data = request.POST.get('slot_str')
                #weekday,start_time = get_recur_time_day(data)
                #print (data)
                start_time = get_date_time(data)
                mins_added = timedelta(minutes = SLOT_DURATION)
                end_time = start_time + mins_added
                
                othertutor_id = request.POST.get('othertutor_id')


                try:
                    other_tutor = Tutoriacc_tutor.objects.get(tu_user_id = othertutor_id)
                    tutor_event = Tutoriacc_Event()
                    tutor_event.evn_description = request.POST.get('description')
                    tutor_event.evn_tutee = Tutoriacc_user.objects.get(acc_user = request.user)
                    tutor_event.evn_tutor = other_tutor

                    tutor_event.start_time = start_time
                    tutor_event.end_time = end_time
                    tutor_event.evn_subject = request.POST.get('subject_str')

                    tutor_event.save()
                    return HttpResponse("SUCCESS")

                except Tutoriacc_tutor.DoesNotExist:
                    #not a tutor
                    return HttpResponse("ERROR")
            else:
                return HttpResponse("NOT FULLY APPROVED")            
        except Tutoriacc_user.DoesNotExist:
            return HttpResponse("NO PERMISSION")
            # no user create user first
    else:
        return HttpResponse("NO PERMISSION")

def acceptSlots(request):

    event_id = request.POST.get('event_id')
    print("event_id:"+event_id)

    if  request.user.is_authenticated:

        try:
            tutor = Tutoriacc_tutor.objects.get(tu_user__acc_user = request.user)

            try:
                event_obj = Tutoriacc_Event.objects.get(id = int(event_id))
                if( event_obj.evn_tutor == tutor) : #it is for tutee
                    operation = request.POST.get('isAccept')

                    if (operation == "1"):
                        event_obj.evn_status_str ="Accepted"
                    elif  (operation == "0"):
                        event_obj.evn_status_str ="Rejected"

                    comments = request.POST.get('comments')
                    
                    if len(comments)>0:
                        event_obj.evn_description =  event_obj.evn_description +"\n Tutor:"+ comments  
                    event_obj.evn_net_meeting =  request.POST.get('ev_link') 

                    event_obj.save()
                    return HttpResponse ("SUCCESS") 

                else:
                    return HttpResponse("ERROR")
            except Tutoriacc_Event.DoesNotExist:
                #not a event
                return HttpResponse("ERROR")
        except Tutoriacc_tutor.DoesNotExist:
            return HttpResponse("NO PERMISSION")
    else:
        return HttpResponse("NO PERMISSION")


def cancelSlots(request):

    event_id = request.POST.get('event_id')
    comments = request.POST.get('comments') # for message

    if  request.user.is_authenticated:

        try:
            user = Tutoriacc_user.objects.get(acc_user = request.user)

            try:
                event_obj = Tutoriacc_Event.objects.get(id = int(event_id))
                if( event_obj.evn_tutee.acc_user == request.user) : #it is for tutee
                    event_obj.delete()
                else:
                    return HttpResponse("NO PERMISSION")
                return HttpResponse ("SUCCESS") 

            except Tutoriacc_Event.DoesNotExist:
                #not a tutor
                return HttpResponse("ERROR")
        except Tutoriacc_user.DoesNotExist:
            return HttpResponse("NO PERMISSION")
            # no user create user first
    else:
        return HttpResponse("NO PERMISSION")



## Message pages

def archiveConv(request):
    #other_user_id = request.GET.get('uid')
    conv_id = request.POST.get('conv_id')

    print("conv="+conv_id)

    if  isAuthentcated(request):
        try:
            user = Tutoriacc_user.objects.get(acc_user = request.user)
            conv_user = Tutoriacc_conversations_user.objects.get(conv_user = user , conversations__id= conv_id)

            # tu_msg = Tutoriacc_messages()

            # tu_msg.conversations = conv_user.conversations
            # tu_msg.sender_user = user
            # tu_msg.messages = user.acc_firstname + " left the chat!  He/She won't see your messages till hi/she restart the chat."
            # tu_msg.save()
            conv_user.start_user_arch = True
            conv_user.save()

            active_conv_users = Tutoriacc_conversations_user.objects.filter(start_user_arch = False , conversations__id= conv_id)

            if not active_conv_users:
                conv_user.conversations.delete() # delete all conv

            return HttpResponse('SUCCESS')

        except Tutoriacc_user.DoesNotExist:
            return HttpResponse('NO PERMISSION')
            # no user create user first
        except Tutoriacc_conversations_user.DoesNotExist:
            return HttpResponse('Error: failed to find the chat')

    else:
        return HttpResponse('NO PERMISSION')

def conversations(request):

    if  isAuthentcated(request):
        try:
            user = Tutoriacc_user.objects.get(acc_user = request.user)

            conv_user_list = Tutoriacc_conversations_user.objects.filter(Q(conv_user=user)& Q(start_user_arch=False))

            response_str=''

            for conv_user in conv_user_list:
                print("find conv")

                new_msg = 0

                if conv_user.conversations.last_chat:
                    if conv_user.acc_last_chat_check:
                        if conv_user.conversations.last_chat > conv_user.acc_last_chat_check:
                            new_msg = 1

                response_str=response_str+"^"+str(conv_user.conversations.id)+"|"+str(new_msg)+"|"

                other_conv_list = Tutoriacc_conversations_user.objects.filter(conversations = conv_user.conversations)
        
                is_no_other = True
                for other_conv in other_conv_list:
                    #there shall be only two
                    if other_conv.conv_user != conv_user.conv_user:
                        response_str = response_str+"~"+other_conv.conv_user.acc_firstname+"#"+other_conv.conv_user.acc_lastname+"#"\
                            +other_conv.conv_user.acc_avatar
                        is_no_other = False
                        break
                if is_no_other:
                    response_str = response_str+"~##"
                
                last_chat_time =""
                if conv_user.conversations.last_chat:
                    last_chat_time = conv_user.conversations.last_chat.strftime('%B %d')

                response_str=response_str+"|"+conv_user.conversations.last_message+"|"+last_chat_time+"|"

            print("conv str:"+response_str)
            return HttpResponse(response_str)
        except Tutoriacc_user.DoesNotExist:
            return HttpResponse('NO PERMISSION')
            # no user create user first
    else:
        return HttpResponse('NO PERMISSION')


def messageUser(request):#start the conversation

    #my_dictionary={}
    other_user_id = request.GET.get('uid')
    

    if  isAuthentcated(request): 
        try:
            user = Tutoriacc_user.objects.get(acc_user = request.user)
            #updateDictionaryWithUserInfo(request,my_dictionary)
            try:
                other_user = Tutoriacc_user.objects.get(acc_user_id = other_user_id)
                #my_dictionary.update({"other_user":other_user})

                conv = findConv(user, other_user, True)

                response_str = str(conv.id)+"^"+other_user.acc_firstname+"^"+other_user.acc_lastname+"^"+other_user.acc_avatar
                if conv.last_chat:
                    response_str=response_str+"^1"
                else:
                    response_str=response_str+"^0"

                print("find conv:"+response_str)

                return HttpResponse(response_str)
            except Tutoriacc_user.DoesNotExist:
                return HttpResponse('Chat target does not exist')

        except Tutoriacc_user.DoesNotExist:
            return HttpResponse('NO PERMISSION')
            # no user create user first
    else:
        return HttpResponse('NO PERMISSION')


def sendMessage(request):


    if request.method == 'POST':
        if  request.user.is_authenticated:

            conv_id = request.POST.get('conv_id')
            print("send message conv_id" + conv_id)

            try:
                user = Tutoriacc_user.objects.get(acc_user = request.user)
 
                try:
                    conv = Tutoriacc_conversations.objects.get(id = conv_id)
                    conv_user = Tutoriacc_conversations_user.objects.get(conversations = conv, conv_user = user)


                    if conv_user.start_user_arch:
                        # tu_msg = Tutoriacc_messages()
                        # tu_msg.conversations = conv

                        # tu_msg.sender_user = user
                        # tu_msg.messages = user.acc_firstname +" restart the chat."
                        # tu_msg.save()
                        conv_user.start_user_arch = False
                        conv_user.save()

                    tu_msg = Tutoriacc_messages()

                    tu_msg.conversations = conv
                    tu_msg.sender_user = user
                    tu_msg.messages = request.POST.get('sendMsg')
                    tu_msg.save()

                    conv.last_chat=datetime.now()
                    conv.last_message= tu_msg.messages 
                    conv.save()



                    # decide later if we shall do this to un-block from all others
                    # conv_users = Tutoriacc_conversations_user.objects.filter(conversations = conv)

                    # for single_conv_user in conv_users:
                    #     single_conv_user.start_user_arch = False
                    #     single_conv_user.save()


                    return HttpResponse ("SUCCESS")                       

                except Tutoriacc_conversations.DoesNotExist:
                    print("no conv  here")
                    return HttpResponse('ERROR:Chat does not exist')
                except Tutoriacc_conversations_user.DoesNotExist:
                    print("no conv  heere")
                    return HttpResponse('NO PERMISSION')
                    
            except Tutoriacc_user.DoesNotExist:
                return HttpResponse('NO PERMISSION')

                # no user create user first

        else:
            return HttpResponse('NO PERMISSION')
    else:
        return HttpResponse('NO PERMISSION')


def getMessages(request):
    conv_id = request.GET.get('conv_id')
    last_msg_id = request.GET.get('last_msg_id')

    print('conv:'+conv_id+" last_id:"+ last_msg_id)

    if  request.user.is_authenticated:
        try:
            response_str=""
            conv_messages = Tutoriacc_messages.objects.filter(conversations__id = conv_id,id__gt=last_msg_id).order_by('-id')[:25][::-1]
            for msg in conv_messages:  
                person_display_name = msg.sender_user.acc_firstname
                
                if(msg.sender_user.acc_user == request.user):
                    person_display_name = "Me"
                

                response_str = response_str+"^"+person_display_name + "|" + msg.messages+"|"+str(msg.message_time.timestamp())+"|"+str(msg.id)+"|"+msg.message_time.strftime('%b %d,%Y %H:%M')

            this_conv_users = Tutoriacc_conversations_user.objects.filter(conversations__id = conv_id)

            other_user_online_status =0 #0 offline, 1 online, 2 left
            for this_conv_user in this_conv_users:
                if this_conv_user.conv_user.acc_user != request.user:

                    if this_conv_user.start_user_arch:
                        other_user_online_status = 2
                        response_str = "2~" + response_str # left

                    else:
                        #find if he is online
                        all_conv_users = Tutoriacc_conversations_user.objects.filter(conv_user__acc_user = this_conv_user.conv_user.acc_user)
                        for all_conv_user in all_conv_users:
                            #find the other guy
                            diff_time = datetime.now() - all_conv_user.acc_last_chat_check.replace(tzinfo=None)
                            if diff_time.total_seconds() < 20: # 5 min
                                response_str = "1~" + response_str # online
                                other_user_online_status = 1
                                break
                    break
            
            if other_user_online_status == 0:
                response_str = "0~" + response_str #not online

            print(response_str)
               

            try:
                conv_user = Tutoriacc_conversations_user.objects.get( conversations__id = conv_id, conv_user__acc_user = request.user)
                conv_user.acc_last_chat_check = datetime.now()
                conv_user.save()
            except Tutoriacc_conversations_user.DoesNotExist:
                print("not a conv user")
                # no user create user first   

            return HttpResponse (response_str)                       

        except Tutoriacc_messages.DoesNotExist:
            print("no message!"+str(conv_id))
            # no user create user first
    else: 
        return HttpResponse('NO PERMISSION')

## supporting functions
def isAuthentcated(request):
    if  request.user.is_authenticated:

        try:
            user = Tutoriacc_user.objects.get(acc_user = request.user)
            return True
        except Tutoriacc_user.DoesNotExist:
            print("not authenticated")
            # no user create user first
    return False


def isAdminAuthentcated(request):
    if  request.user.is_authenticated:

        try:
            user = Tutori_admin.objects.get(admin_user = request.user)
            return True
        except Tutori_admin.DoesNotExist:
            print("not admin authenticated")
            # no user create user first
    return False


def createSubjectProfileDisplay (subjects, Prefix):
    course_list = subjects.split("|")
    course_display_dict={}
    for course in course_list:
        if course !="":
            course_info = course.split(":")
            #print(str(course_info))
            if course_info[0] in course_display_dict:
                course_display_dict[course_info[0]] = course_display_dict[course_info[0]]+","+course_info[1]
            else:
                course_display_dict.update({course_info[0]: Prefix+course_info[1]})
    return course_display_dict



def updateDictionaryWithUserInfo(request, my_dictionary):
    my_dictionary.update({"isUser" : "true"})

    try:
        tutor = Tutoriacc_tutor.objects.get(tu_user__acc_user = request.user)
        my_dictionary.update({"tutor" : tutor})
    except Tutoriacc_tutor.DoesNotExist:
        #not a tutor
        pass

    try:
        user = Tutoriacc_user.objects.get(acc_user = request.user)
        my_dictionary.update({"tu_user" : user})
    except Tutoriacc_user.DoesNotExist:
        pass        # no user create user first


def findConv (me, other, isCreateNew):

    conv = None

    convs_users =  Tutoriacc_conversations_user.objects.filter(conv_user = me)

    if convs_users.exists():
        
        for convs_user in convs_users:
            
            other_conv_users =  Tutoriacc_conversations_user.objects.filter(conv_user = other, conversations = convs_user.conversations )

            if other_conv_users.exists():
                conv = convs_user.conversations
                break

    if conv:
        return conv
    else:

        conv = Tutoriacc_conversations()
        conv.save()
        convs_users = Tutoriacc_conversations_user()
        convs_users.conversations = conv
        convs_users.conv_user = me
        convs_users.save()
        convs_users = Tutoriacc_conversations_user()
        convs_users.conversations = conv
        convs_users.conv_user = other
        convs_users.save()
        return conv



def findTheOther(conv, user):
    other_user_id = -100
    if (conv.start_user_id == user.id):
        print("the other is the other:"+str(conv.other_user_id))
        other_user_id = conv.other_user_id
    elif (conv.other_user_id == user.id):
        print("the starter is the other:"+str(conv.start_user_id))
        other_user_id = conv.start_user_id
    else:
        print("this is not the conv"+str(conv)+str(user))
    
    if(other_user_id != -100):
        try:
            user = Tutoriacc_user.objects.get(id = other_user_id)
            return user
        except Tutoriacc_user.DoesNotExist:
            print("not user found")            
    


def get_date(req_day):
    if req_day:
        year, month = (int(x) for x in req_day.split('-'))
        return date(year, month, day=1)
    return datetime.today()

def get_days_for_month_year(data):
    if data:
        year, month = (int(x) for x in data.split('-'))
        return calendar.monthcalendar(year, month)

    return calendar.monthcalendar(datetime.today().year, datetime.today().month) 

def get_date_day(req_day):
    if req_day:
        year, month, day , hr, minu = (int(x) for x in req_day.split('-'))
        return datetime(year, month, day, hr, minu, 0)
    return None

def get_time_day(req_time):
    if req_time:
        hr, minu = (int(x) for x in req_time.split(':'))
        return time(hr, minu, 0)
    return None

def get_recur_time_day(req_weekday_time):
    if req_weekday_time:
        weekday,time_str = ( x for x in req_weekday_time.split('|'))

        hr, minu = (int(x) for x in time_str.split(':'))
        return int(weekday), time(hr, minu, 0)
    return None

def get_date_time(req_weekday_time):
    if req_weekday_time:
        return datetime.strptime(req_weekday_time,'%m/%d/%Y, %H:%M %a')
    return None

def prev_month(d):
    first = d.replace(day=1)
    prev_month = first - timedelta(days=1)
    month = 'month=' + str(prev_month.year) + '-' + str(prev_month.month)
    return month

def next_month(d):
    days_in_month = calendar.monthrange(d.year, d.month)[1]
    last = d.replace(day=days_in_month)
    next_month = last + timedelta(days=1)
    month = 'month=' + str(next_month.year) + '-' + str(next_month.month)
    return month


#def editStudentProfile(request): # it will also be used as view profile for normal users

#     if  request.user.is_authenticated:

#         if request.method == 'POST':
#             try:
#                 tutor = Tutoriacc_user.objects.get(acc_user = request.user)
#             except Tutoriacc_user.DoesNotExist:
#                 print('not exist!!!')
#                 tutor = Tutoriacc_user()                
#                 tutor.acc_user = request.user
#             tutor.acc_avatar = request.user.socialaccount_set.all()[0].get_avatar_url()
#             tutor.acc_firstname = request.POST.get('firstname')
#             tutor.acc_lastname = request.POST.get('lastname')
#             tutor.acc_aboutme = request.POST.get('aboutme')
#             tutor.acc_grade = request.POST.get('grade')
#             tutor.save()
#             if request.POST.get('isTutor') == 'true':
#                 return HttpResponseRedirect('/tutor-1') # Redirect after POST
#             else:
#                 return HttpResponseRedirect('/') # Redirect after POST
#         else:
#             print ("it is not post")
#             my_dictionary = {}
#             try:
#                 tu_user = Tutoriacc_user.objects.get(acc_user = request.user)
#                 print ("it is existing user")

#                 my_dictionary.update({"tu_user" : tu_user})
#                 my_dictionary.update({"isUser" : "true"})


#                 try:
#                     tutor = Tutoriacc_tutor.objects.get(tu_user = tu_user)
#                     return HttpResponseRedirect('/editProfile') # Redirect to tutor profile page
#                 except Tutoriacc_tutor.DoesNotExist:
#                     print ("Not a tutor")

#             except Tutoriacc_user.DoesNotExist:
#                 print('not exist!!!')
 
#             return render(request, 'student.html', my_dictionary)
#     else:
#         return HttpResponseRedirect('/?errorlogin=1') # Redirect to home

# def editProfile(request):
    
#     if  request.user.is_authenticated :
#         if request.method == 'POST':
#             try:
#                 tu_user = Tutoriacc_user.objects.get(acc_user = request.user)
#             except Tutoriacc_user.DoesNotExist:
#                 print('not exist!!!')
#                 return HttpResponseRedirect('/?errorlogin=1') # Redirect to home
#             tu_user.acc_avatar = request.user.socialaccount_set.all()[0].get_avatar_url()
#             tu_user.acc_firstname = request.POST.get('firstname')
#             tu_user.acc_lastname = request.POST.get('lastname')
#             tu_user.acc_aboutme = request.POST.get('aboutme')
#             tu_user.acc_grade = request.POST.get('grade')
#             tu_user.save()

#             try:
#                 tutor = Tutoriacc_tutor.objects.get(tu_user = tu_user)

#             except Tutoriacc_tutor.DoesNotExist:
#                 print("edit profile with new tutor user. shall not be here!!")
#                 #new user
#                 tutor = Tutoriacc_tutor()   
#                 tutor.tu_user = tu_user


#             tutor.acc_subjects =""
#             subject_count = 1
#             while subject_count <= SUBJECT_NUM: 
#                 if request.POST.get('Subject'+str(subject_count)):
#                     tutor.acc_subjects = tutor.acc_subjects+"|"+ request.POST.get('Subject'+str(subject_count))
#                 subject_count = subject_count +1    
#             print("subjects:"+tutor.acc_subjects )
# #            tutor.acc_info = request.POST.get('extra_info') 
#  #           tutor.acc_calendly_link = request.POST.get('calendly_link')
#  #           tutor.acc_calendly_60_link = request.POST.get('calendly_link_60')

#             tutor.save()

#             ## temp code

#             return HttpResponseRedirect('/profile') # Redirect after POST

#         else:
#             try:
#                 tu_user = Tutoriacc_user.objects.get(acc_user = request.user)
#                 my_dictionary = {"tu_user" : tu_user}

#                 try:
#                     tutor =  Tutoriacc_tutor.objects.get(tu_user = tu_user)   
#                     my_dictionary.update({"tutor":tutor})
#                 except Tutoriacc_tutor.DoesNotExist:
#                     print("Not a tutor")
#                     return HttpResponseRedirect('/editStudentProfile') # Redirect student profile
                
#                 my_dictionary.update({"isUser" : "true"})

#                 return render(request, 'edit-profile.html', my_dictionary)
#             except Tutoriacc_user.DoesNotExist:
#                 print("no user")
#                 return HttpResponseRedirect('/?errornouser=1') # Redirect home
#     else:
#         return HttpResponseRedirect('/?errorlogin=1') # Redirect to home



    
# def profile(request):

#     if  request.user.is_authenticated:
#         try:
#             tu_user = Tutoriacc_user.objects.get(acc_user = request.user)
#             my_dictionary = {"tu_user" : tu_user}
#             my_dictionary.update({"isUser" : "true"})


#             try:
#                 tutor =  Tutoriacc_tutor.objects.get(tu_user = tu_user)   
#                 my_dictionary.update({"tutor":tutor})
#                 course_display_dict = createSubjectProfileDisplay(tutor.acc_subjects)
#                 my_dictionary.update({"course_dict": course_display_dict})               
#             except Tutoriacc_tutor.DoesNotExist:
#                 print("Not a tutor")
            
#             return render(request, 'your-profile.html', my_dictionary)
#         except Tutoriacc_user.DoesNotExist:
#             print("no user")
#             return HttpResponseRedirect('/?error=nouser') # Redirect home
#     else:
#         return HttpResponseRedirect('/?errorlogin=1') # Redirect to home



# def tutor1(request):
#     if  isAuthentcated(request):

#         if request.method == 'POST':

#             try:
#                 tutor = Tutoriacc_tutor.objects.get(tu_user__acc_user = request.user)

#             except Tutoriacc_tutor.DoesNotExist:
#                 #new user
#                 try:
#                     user = Tutoriacc_user.objects.get(acc_user = request.user)
#                     tutor = Tutoriacc_tutor()   
#                     tutor.tu_user = user
#                 except Tutoriacc_user.DoesNotExist:
#                     # no user create user first
#                     return HttpResponseRedirect('/tutor') # Redirect after POST

#             tutor.acc_subjects =""
#             subject_count = 1
#             while subject_count <= SUBJECT_NUM: 
#                 if request.POST.get('Subject'+str(subject_count)):
#                     tutor.acc_subjects = tutor.acc_subjects+"|"+ request.POST.get('Subject'+str(subject_count))
#                 subject_count = subject_count +1    
#             print("subjects:"+tutor.acc_subjects )
#             tutor.acc_pasttutor = request.POST.get('experence')
#             tutor.acc_info = request.POST.get('extra_info') 
#  #           tutor.acc_calendly_link = request.POST.get('calendly_link')
#  #           tutor.acc_calendly_60_link = request.POST.get('calendly_link_60')

#             tutor.save()
#             return HttpResponseRedirect('/tutor-2') # Redirect after POST

#         else: # not post
#             print ("it is not post")
#             my_dictionary = {}
#             my_dictionary.update({"isUser" : "true"})

#             try:
#                 tutor = Tutoriacc_tutor.objects.get(tu_user__acc_user = request.user)
#                 my_dictionary.update({"info_user" : tutor})

#             except Tutoriacc_tutor.DoesNotExist:
#                 print('not exist!!!')
 
#             return render(request, 'tutor-1.html', my_dictionary)
#     else:
#         return HttpResponseRedirect('/?errorlogin=1') # Redirect to home
# def inviteAGroup(email_pattern, recieving_email, admin ,num_counts):

#     invitation = Tutori_invited_list()
#     invitation.gmail_setting = email_pattern
#     invitation.is_tutor = False 
#     invitation.invitation_recievor = recieving_email
#     one_time_code = OTP_generator()
#     print(invitation.gmail_setting+ "'s OTP="+one_time_code)
#     hashed_code = hashlib.sha256(one_time_code.encode('utf-8')).hexdigest()
#     invitation.one_time_activation_code = hashed_code 
#     invitation.admin = admin
#     invitation.activation_code_use_count = int(num_counts)
#     invitation.save()

    # send email

    # subject = 'Join Tutori Program.'
    # message = ' Hi, there, \n\n Please help to distribute activation code to who are intersted in joining the Tutori program and start learning.'\
    #     + ' \n\n Please forward following activation code for their registration: ' + one_time_code + '. There are currently ' +num_counts+' spot for interested students' \
    #     + ' \n Please contact us if they run into any issues. \n\nThanks From Tutori Team.'

    # email_from = settings.EMAIL_HOST_USER
    # recipient_list = [recieving_email,]
    
    # t1 = threading.Thread(target=send_mail, args=[subject, message, email_from, recipient_list])
    # t1.start()
