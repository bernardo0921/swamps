from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
import requests
from django.conf import settings
import json
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .forms import CustomUserCreationForm


# from django.shortcuts import render
# from django.contrib.auth.decorators import login_required
# import requests
# from django.conf import settings
# import json
from datetime import datetime



def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'login.html')

@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('login')

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful!')
            return redirect('dashboard')  # Change to your dashboard URL name
        else:
            messages.error(request, 'Registration failed. Please correct the errors below.')
    else:
        form = CustomUserCreationForm()
    return render(request, 'register.html', {'form': form})

@login_required
def dashboard(request):
    # ThingSpeak API configuration
    CHANNEL_ID = '2735541'
    THINGSPEAK_READ_API_KEY = 'OQELH67Y8R5KFCGA'
    
    try:
        # Fetch data for all fields
        url = f'https://api.thingspeak.com/channels/{CHANNEL_ID}/feeds.json'
        params = {
            'api_key': THINGSPEAK_READ_API_KEY,
            'results': 24  # Last 24 readings
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise an exception for bad status codes
        data = response.json()
        
        # Process the data for the dashboard
        feeds = data.get('feeds', [])
        
        # Convert timestamps and handle missing or invalid data
        timestamps = []
        tds_readings = []
        ph_readings = []
        flow_readings = []
        turbidity_readings = []
        
        for feed in feeds:
            # Convert timestamp to readable format
            try:
                timestamp = datetime.strptime(feed['created_at'], '%Y-%m-%dT%H:%M:%SZ')
                timestamps.append(timestamp.strftime('%Y-%m-%d %H:%M:%S'))
            except:
                continue
                
            # Handle each field, using None for missing/invalid data
            try:
                tds_readings.append(float(feed['field1']) if feed['field1'] else None)
            except:
                tds_readings.append(None)
                
            try:
                ph_readings.append(float(feed['field2']) if feed['field2'] else None)
            except:
                ph_readings.append(None)
                
            try:
                flow_readings.append(float(feed['field3']) if feed['field3'] else None)
            except:
                flow_readings.append(None)
                
            try:
                turbidity_readings.append(float(feed['field4']) if feed['field4'] else None)
            except:
                turbidity_readings.append(None)
        
        # Get latest valid readings
        latest_tds = next((reading for reading in reversed(tds_readings) if reading is not None), 'N/A')
        latest_ph = next((reading for reading in reversed(ph_readings) if reading is not None), 'N/A')
        latest_flow = next((reading for reading in reversed(flow_readings) if reading is not None), 'N/A')
        latest_turbidity = next((reading for reading in reversed(turbidity_readings) if reading is not None), 'N/A')
        
        context = {
            'timestamps': json.dumps(timestamps),
            'tds_readings': json.dumps(tds_readings),
            'ph_readings': json.dumps(ph_readings),
            'flow_readings': json.dumps(flow_readings),
            'turbidity_readings': json.dumps(turbidity_readings),
            'latest_tds': latest_tds,
            'latest_ph': latest_ph,
            'latest_flow': latest_flow,
            'latest_turbidity': latest_turbidity,
        }
        
    except requests.RequestException as e:
        context = {
            'error': f"Error connecting to ThingSpeak API: {str(e)}"
        }
    except Exception as e:
        context = {
            'error': f"Error processing data: {str(e)}"
        }
    
    return render(request, 'dashboard.html', context)