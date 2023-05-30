from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from loginapp import settings
from django.core.mail import send_mail, EmailMessage
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from . tokens import generate_token
def home(request):
    return render(request, 'authentication/index.html')

def signin(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['pass1']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            fname = user.first_name
            return render(request, 'authentication/index.html', {'fname': fname})
        else:
            messages.error(request, 'Bad Credientals')
            return redirect('home')
    return render(request, 'authentication/signin.html')

def signup(request):
    if request.method == 'POST':
      # username = request.POST.get('username')
      username = request.POST['username']
      fname = request.POST['fname']
      lname = request.POST['lname']
      email = request.POST['email']
      pass1 = request.POST['pass1']
      pass2 = request.POST['pass2']

      if User.objects.filter(username=username):
          messages.error(request, 'Username Already Exists')
          return redirect('home')

      if len(username)>10:
          messages.error(request, 'Username should be less than 10')   
          return redirect('home')
      
      if pass1 != pass2:
          messages.error(request, 'Password did not matched')
          return redirect('home')
      
      if not username.isalnum():
          messages.error(request, 'Username should be alphanumeric')
          return redirect('home')

      myuser = User.objects.create_user(username, email, pass1)
      myuser.first_name = fname
      myuser.last_name = lname
      myuser.is_active = False
      myuser.save()

      messages.success(request, 'Your account has been successfully created. We have sent you a confirmation email. Please active your account by confirming it.')

      # Welcome Email
      subject = 'Hello To Django Login'
      message = 'Hello ' + myuser.first_name + ' !! \n Welcome to Django Login \n\n Thank you for visiting our website. \n We also sent you another email. Please confirm your email.'  
      from_email = settings.EMAIL_HOST_USER
      to_list = [myuser.email]
      send_mail(subject, message, from_email, to_list, fail_silently=True)

      # Email Address Verification
      current_site = get_current_site(request)
      subject1 = 'Confirm Your Email @ Login App'
      message1 = render_to_string('email_confirmation.html',{
          'name': myuser.first_name,
          'domain': current_site.domain,
          'uid': urlsafe_base64_encode(force_bytes(myuser.pk)),
          'token': generate_token.make_token(myuser)
      })
      email = EmailMessage(
          subject1,
          message1,
          settings.EMAIL_HOST_USER,
          [myuser.email]
      )
      email.fail_silently = True
      email.send()
      return redirect('signin')

    return render(request, 'authentication/signup.html')

def signout(request):
    logout(request)
    messages.success(request, 'logged out successfully')
    return redirect('home')

def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        myuser = User.objects.get(pk=uid)
    except (ValueError, TypeError, OverflowError, User.DoesNotExist):
        myuser = None
    
    if myuser is not None and generate_token.check_token(myuser, token):
        myuser.is_active = True
        myuser.save()
        login(request, myuser)
        return redirect('home')
    return render(request, 'activation_failed.html')