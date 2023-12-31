import uuid
import boto3
import os
from django.shortcuts import render, redirect
from django.views.generic import ListView, DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.urls import reverse
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import Wedding, Event, Guest, Photo
from .forms import EventForm, GuestForm, UserForm, ProfileForm

# Create your views here.
def home(request):
    return render(request, 'home.html')

@login_required
def weddings_detail(request, wedding_id):
    wedding = Wedding.objects.get(id=wedding_id)
    event_form = EventForm()
    guest_form = GuestForm()
    return render(request, 'main_app/wedding_detail.html', {'wedding': wedding, 'event_form': event_form, 'guest_form': guest_form})

@login_required
def add_event(request, wedding_id):
    form = EventForm(request.POST)
    if form.is_valid():
        new_event = form.save(commit=False)
        new_event.wedding_id = wedding_id
        new_event.save()
    return redirect('weddings_detail', wedding_id=wedding_id)

@login_required
def add_photo(request, event_id):
    # photo-file will be the "name" attribute on the <input type="file">
    photo_file = request.FILES.get('photo-file', None)
    if photo_file:
        s3 = boto3.client('s3')
        # need a unique "key" for S3 / needs image file extension too
        key = uuid.uuid4().hex[:6] + photo_file.name[photo_file.name.rfind('.'):]
        # just in case something goes wrong
        try:
            bucket = os.environ['S3_BUCKET']
            s3.upload_fileobj(photo_file, bucket, key)
            # build the full url string
            url = f"{os.environ['S3_BASE_URL']}{bucket}/{key}"
            # we can assign to event_id or event (if you have a event object)
            Photo.objects.create(url=url, event_id=event_id)
        except Exception as e:
            print('An error occurred uploading file to S3')
            print(e)
    return redirect('events_detail', pk=event_id)

@login_required
def add_guest(request, wedding_id):
    form = GuestForm(request.POST)
    if form.is_valid():
        new_guest = form.save(commit=False)
        new_guest.wedding_id = wedding_id
        new_guest.save()
    return redirect('weddings_detail', wedding_id=wedding_id)

@login_required
def assoc_guest(request, event_id, guest_id):
    event = Event.objects.get(id=event_id)
    event.guests.add(guest_id)
    return redirect('events_detail', pk=event_id)

@login_required
def unassoc_guest(request, event_id, guest_id):
    event = Event.objects.get(id=event_id)
    event.guests.remove(guest_id)
    return redirect('events_detail', pk=event_id)

class WeddingList(LoginRequiredMixin, ListView):
    def get_queryset(self):
        return Wedding.objects.filter(profiles__id=self.request.user.profile.id)

class WeddingCreate(LoginRequiredMixin, CreateView):
    model = Wedding
    fields = ['name', 'description']

    def form_valid(self,form):
        #Many to Many id troubleshoot
        new_wedding=form.save()
        new_wedding.profiles.add(self.request.user.profile.id)
        new_wedding.save()
        return super().form_valid(form)

class WeddingDelete(LoginRequiredMixin, DeleteView):
    model = Wedding
    success_url = '/weddings/'

class WeddingUpdate(LoginRequiredMixin, UpdateView):
    model = Wedding
    fields = ['description']

class EventDetail(LoginRequiredMixin, DetailView):
    model = Event

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        event_guest_id_list = self.object.guests.all().values_list('id')
        wedding_guests = Guest.objects.filter(wedding__id=self.object.wedding.id)
        wedding_guests_not_invited_to_event = wedding_guests.exclude(id__in=event_guest_id_list)
        context["wedding_guests_not_invited_to_event"] = wedding_guests_not_invited_to_event
        return context

class EventDelete(LoginRequiredMixin, DeleteView):
    model = Event
    def get_success_url(self):
        wedding = self.object.wedding 
        return reverse('weddings_detail', kwargs={'wedding_id': wedding.id})
    
class EventUpdate(LoginRequiredMixin, UpdateView):
    model = Event
    fields = ['description', 'start_date_time', 'end_date_time', 'venue']
    
def signup(request):
    error_message =''
    if request.method == 'POST':
        user_form = UserForm(request.POST)
        profile_form = ProfileForm(request.POST)
        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save()
            profile = profile_form.save(commit=False)
            profile.user_id = user.id
            profile = profile_form.save()
            login(request, user)
            return redirect('weddings_list')
        else:
            error_message = 'Invalid sign up - try again'
    user_form = UserForm()
    profile_form = ProfileForm()
    context = {'user_form': user_form, 'profile_form': profile_form,'error_message': error_message}
    return render(request, 'registration/signup.html', context)