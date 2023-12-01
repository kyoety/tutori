from django.db import models
from PIL import Image, ExifTags
from io import BytesIO
from django.core.files.base import ContentFile
from datetime import datetime, time
from django.contrib.auth.models import User

import datetime

# Create your models here.

class Tutoriacc_user(models.Model):
    acc_user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    acc_avatar = models.CharField(max_length = 100, blank = False)
    acc_firstname = models.CharField(max_length = 20, blank = False)
    acc_lastname = models.CharField(max_length = 20, blank = False)
    acc_aboutme = models.CharField(max_length = 250, blank = True, null = True)
    acc_grade =  models.IntegerField( blank = True, null = True)
    acc_creationdate = models.DateTimeField(auto_now_add = True)
    #is_blocked = models.BooleanField( blank = False,  default = False)
    homeschool = models.CharField(max_length = 100, blank = True, null = True)
    is_approved = models.BooleanField( blank = False,  default = False)

class Tutoriacc_tutor(models.Model):
    tu_user = models.OneToOneField(Tutoriacc_user, on_delete=models.CASCADE, primary_key=True)
    acc_subjects = models.CharField(max_length = 500, blank = True, null = True)

 #   acc_info = models.CharField(max_length = 500, blank = True, null = True) #not in use
 #   acc_pasttutor = models.CharField(max_length = 3, blank = True, null = True)
#    acc_account_approved = models.BooleanField( blank = True,  default = False)
 #   acc_calendly_link = models.CharField(max_length = 500, default='', blank = True, null = True)
 #   acc_calendly_60_link = models.CharField(max_length = 500, default='', blank = True, null = True)



class Tutori_admin(models.Model): #independent of user
    admin_user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    acc_creationdate = models.DateTimeField(auto_now_add = True)

class Tutori_invited_list(models.Model): #to invite new member
    gmail_setting = models.CharField(max_length = 50, blank = False, null = False) #email or domain name to validate the invitation. tutor must use email
    one_time_activation_code = models.CharField(max_length = 64, blank = False, null = False, primary_key=True) #sha256 hash of the code, resend it will trigger re-gen code
    firstname = models.CharField(max_length = 20, blank = False,default = "")
    lastname = models.CharField(max_length = 20, blank = False,default = "")
    aboutme = models.CharField(max_length = 250, blank = True, null = True)
    grade =  models.IntegerField( blank = True, null = True)
    subjects = models.CharField(max_length = 200, blank = True, null = True)
    admin = models.CharField(max_length = 50, blank = False, null = False)
    homeschool = models.CharField(max_length = 100, blank = True, null = True)
    # not used for now
    #activation_code_use_count = models.IntegerField( blank = False, default = -1)
    #is_tutor = models.BooleanField( blank = False,  default = True)
#    invitation_recievor = models.CharField(max_length = 50, blank = True, null = True) # who recieve the invite to share with others
    invite_time = models.DateTimeField(auto_now_add = True, null = True)
    valid_days = models.IntegerField( blank = False, default = 90)

# message data
class Tutoriacc_conversations(models.Model):
    last_chat = models.DateTimeField( null = True, blank = True)
    last_message = models.CharField(max_length = 200, blank = True)


class Tutoriacc_conversations_user(models.Model):
    conversations = models.ForeignKey(Tutoriacc_conversations, on_delete = models.CASCADE)
    conv_user = models.ForeignKey(Tutoriacc_user, on_delete = models.CASCADE)
    start_user_arch = models.BooleanField( blank = False,  default = False) #indicator of left
    acc_last_chat_check = models.DateTimeField(auto_now_add = True, null = True)


class Tutoriacc_messages(models.Model):
    conversations = models.ForeignKey(Tutoriacc_conversations, on_delete = models.CASCADE)
    sender_user = models.ForeignKey(Tutoriacc_user, on_delete = models.CASCADE)
    messages = models.TextField(max_length = 200, blank = False)
    message_time = models.DateTimeField(auto_now_add = True)


# calendar event schedule

class Tutoriacc_Event(models.Model): # session
    evn_tutor = models.ForeignKey(Tutoriacc_tutor, on_delete = models.CASCADE)
    evn_tutee = models.ForeignKey(Tutoriacc_user, on_delete = models.CASCADE)
    start_time = models.DateTimeField( null = True)
    end_time = models.DateTimeField( null = True)
    evn_subject = models.CharField(max_length=50 , blank = True, null = True, default ="")
#    evn_duration = models.IntegerField( default = 30, blank = False, null = False)
#    recurweekday = models.IntegerField( default = 0, blank = True, null = True) # used for recur events, more than one ocurranc in a week use two events
#    event_date = models.DateField( blank = True, null = True) # used for none recur events
    evn_description = models.CharField(max_length=200 , blank = False, null = False, default ="")
    evn_status_str = models.CharField( max_length=10, default = "Pending", blank = True, null = True)
    evn_net_meeting= models.CharField( max_length=200, default = "", blank = True, null = True)


class Tutoriacc_TutorSlots(models.Model):
    slot_tutor = models.ForeignKey(Tutoriacc_tutor, on_delete = models.CASCADE)
    start_time = models.TimeField( null = False)
    end_time = models.TimeField( null = False)
    weekday = models.IntegerField( default = 0, blank = False, null = False)
    unique_together = ('slot_tutor', 'weekday')

class Tutoriacc_Dropin_Event(models.Model): # drop in session
    evn_tutor = models.ForeignKey(Tutoriacc_tutor, on_delete = models.CASCADE)
    start_time = models.DateTimeField( null = True)
    end_time = models.DateTimeField( null = True)
    evn_subject = models.CharField(max_length=50 , blank = True, null = True, default ="")
    evn_description = models.CharField(max_length=200 , blank = False, null = False, default ="")
    evn_net_meeting= models.CharField( max_length=200, default = "", blank = True, null = True)

class Tutoriacc_Dropin_Participate(models.Model): # drop in session
    evn_dropin = models.ForeignKey(Tutoriacc_Dropin_Event, on_delete = models.CASCADE)
    evn_tutee = models.ForeignKey(Tutoriacc_user, on_delete = models.CASCADE)


#
# class Tutoriacc_tutor_transcript(models.Model):
#     tutor = models.ForeignKey(Tutoriacc_tutor, on_delete = models.CASCADE)
#     acc_transcript = models.ImageField(upload_to = 'images/', blank = True, null = True)
#
# class Tutor_tutee_session_plan(models.Model):
#     tutor = models.ForeignKey(Tutoriacc_tutor, on_delete = models.CASCADE)
