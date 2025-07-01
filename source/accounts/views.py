from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _
from django.views.generic import View
from django.conf import settings
from .forms import *
from .models import *
import uuid

class GuestOnlyView(View):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(settings.LOGIN_REDIRECT_URL)
        return super().dispatch(request, *args, **kwargs)

class LoginView(GuestOnlyView):
    def get(self, request):
        form = LoginForm()
        return render(request, 'accounts/login.html', {'form': form})

    def post(self, request):
        form = LoginForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            remember_me = form.cleaned_data.get('remember_me')
            
            # Allow login with email or username
            user_obj = None
            if '@' in username:
                try:
                    user_obj = User.objects.get(email=username)
                    username = user_obj.username
                except User.DoesNotExist:
                    messages.error(request, _('Invalid email or password.'))
                    return render(request, 'accounts/login.html', {'form': form})
            
            user = authenticate(username=username, password=password)
            if user:
                if user.is_active:
                    login(request, user)
                    if not remember_me:
                        request.session.set_expiry(0)  # Session expires when browser closes
                    else:
                        request.session.set_expiry(1209600)  # 2 weeks
                    
                    messages.success(request, _('Welcome back, {}!').format(user.first_name or user.username))
                    return redirect('main:index')
                else:
                    # User exists but account is not activated
                    messages.error(request, _('Your account is not activated. Please check your email for the activation link.'))
                    # Optionally, provide a way to resend activation email
                    context = {
                        'form': form,
                        'show_resend_activation': True,
                        'user_email': user.email
                    }
                    return render(request, 'accounts/login.html', context)
            else:
                messages.error(request, _('Invalid username or password.'))
        
        return render(request, 'accounts/login.html', {'form': form})

class RegisterView(GuestOnlyView):
    def get(self, request):
        form = SignUpForm()
        return render(request, 'accounts/register.html', {'form': form})

    def post(self, request):
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # User needs to activate account
            user.save()
            
            # Create user profile
            UserProfile.objects.create(user=user)
            
            # Create activation code
            activation = Activation.objects.create(
                user=user,
                code=str(uuid.uuid4()),
                email=user.email
            )
            
            # Send activation email
            if self.send_activation_email(user, activation.code):
                messages.success(request, _(
                    'Account created successfully! We have sent an activation link to {}. '
                    'Please check your email and click the link to activate your account.'
                ).format(user.email))
            else:
                messages.warning(request, _(
                    'Account created but there was an issue sending the activation email. '
                    'Please contact support.'
                ))
            
            return redirect('accounts:login')
        
        return render(request, 'accounts/register.html', {'form': form})

    def send_activation_email(self, user, activation_code):
        try:
            subject = _('Activate your account')
            message = render_to_string('accounts/activation_email.html', {
                'user': user,
                'activation_code': activation_code,
                'domain': 'localhost:8000',  # Change for production
            })
            send_mail(subject, message, settings.EMAIL_HOST_USER, [user.email])
            return True
        except Exception as e:
            print(f"Email sending failed: {e}")
            return False

class ActivateView(View):
    def get(self, request, activation_code):
        try:
            activation = Activation.objects.get(code=activation_code)
            user = activation.user
            user.is_active = True
            user.save()
            activation.delete()
            
            messages.success(request, _('Account activated successfully! You can now login.'))
            return redirect('accounts:login')
        except Activation.DoesNotExist:
            messages.error(request, _('Invalid or expired activation code.'))
            return redirect('accounts:register')

class ResendActivationView(View):
    def post(self, request):
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email, is_active=False)
            
            # Delete old activation codes
            Activation.objects.filter(user=user).delete()
            
            # Create new activation code
            activation = Activation.objects.create(
                user=user,
                code=str(uuid.uuid4()),
                email=user.email
            )
            
            # Send activation email
            if self.send_activation_email(user, activation.code):
                messages.success(request, _('Activation email sent! Please check your email.'))
            else:
                messages.error(request, _('Failed to send activation email. Please try again.'))
                
        except User.DoesNotExist:
            messages.error(request, _('No inactive account found with this email.'))
        
        return redirect('accounts:login')

    def send_activation_email(self, user, activation_code):
        try:
            subject = _('Activate your account')
            message = render_to_string('accounts/activation_email.html', {
                'user': user,
                'activation_code': activation_code,
                'domain': 'localhost:8000',
            })
            send_mail(subject, message, settings.EMAIL_HOST_USER, [user.email])
            return True
        except Exception as e:
            print(f"Email sending failed: {e}")
            return False

@login_required
def profile_view(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile, user=request.user)
        if form.is_valid():
            # Update user fields
            request.user.first_name = form.cleaned_data['first_name']
            request.user.last_name = form.cleaned_data['last_name']
            request.user.email = form.cleaned_data['email']
            request.user.save()
            
            # Update profile
            form.save()
            messages.success(request, _('Profile updated successfully!'))
            return redirect('accounts:profile')
    else:
        form = ProfileForm(instance=profile, user=request.user)
    
    return render(request, 'accounts/profile.html', {'form': form, 'profile': profile})

class LogoutView(View):
    def get(self, request):
        logout(request)
        messages.success(request, _('You have been logged out successfully.'))
        return redirect('main:index')
