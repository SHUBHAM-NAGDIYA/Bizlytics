from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.db import IntegrityError
from .models import StoreOwneres
from .services.ingestion import process_sales_upload,delete_uploaded_data
from .services.analytics import get_sales_insights
from .services.forecasting import get_revenue_forecast_metrics
from .services.inventory import get_low_stock_alerts
from .services.forecasting_engine import generate_demand_forecast
from .services.stock_recommendation_engine import generate_stock_recommendations
from django.utils import timezone



'''_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _Pages_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _'''
def landing(request):
    return render(request, 'landing.html')



def registration(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        storename = request.POST.get('storename')
        ownername = request.POST.get('ownername')
        city = request.POST.get('city')

        # Basic Validation
        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect('registration')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect('registration')

        try:
            user = User.objects.create_user(
                username=username,
                password=password
            )

            StoreOwneres.objects.create(
                user=user,
                storename=storename,
                ownername=ownername,
                city=city
            )

            messages.success(request, "Registration successful. Please login.")
            return redirect('signin')

        except IntegrityError:
            messages.error(request, "Something went wrong. Try again.")
            return redirect('registration')

    return render(request, 'registration.html')


def signin(request):

    ''' # If already logged in
    if request.user.is_authenticated:
        return redirect('dashboard')'''
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        if not username or not password:
            messages.error(request, "Please enter both username and password.")
            return redirect('signin')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, "Login successful.")
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid credentials. Please try again.")
            return redirect('signin')

    return render(request, 'signin.html')



def signout(request):
    delete_uploaded_data()
    logout(request)
    messages.success(request, "Logged out successfully.")
    return redirect('landing')


@login_required(login_url='signin')
def dashboard(request):
    return render(request, 'dashboard.html')



@login_required(login_url='signin')
def upload_sales(request):
    if request.method == 'POST':

        if not hasattr(request.user, 'storeowneres'):
            messages.error(request, "Store profile not found.")
            return redirect('upload_sales')

        store = request.user.storeowneres
        file = request.FILES.get('uploaded_file')

        if not file:
            messages.error(request, "Please select a file to upload.")
            return redirect('upload_sales')

        try:
            data, status = process_sales_upload(file, store)

            if status == 200:
                messages.success(
                    request,
                    f"Upload successful. {data.get('records_inserted', 0)} records added."
                )
            else:
                messages.error(request, data.get('error', "Something went wrong."))

        except Exception as e:
            messages.error(request, f"Server error: {str(e)}")

        return redirect('upload_sales')

    return render(request, 'uploadsales.html')

@login_required(login_url='signin')
def dashboard(request):
    return render(request, 'dashboard.html')


"""_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ APIs_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _"""
'''@login_required(login_url='signin')
def get_insights(request):
    if request.method == 'GET':
        data = get_sales_insights()
        return JsonResponse(data)'''

@login_required
def get_insights(request):
    store = request.user.storeowneres
    data = get_sales_insights(store)
    return JsonResponse(data)


@login_required(login_url='signin')
def forecast_demand(request):
    if request.method == 'GET':
        store = request.user.storeowneres
        data = get_revenue_forecast_metrics(store)
        return JsonResponse(data)


@login_required(login_url='signin')
def low_stock_alert(request):
    if request.method == 'GET':
        store = request.user.storeowneres
        alerts = get_low_stock_alerts(store)
        return JsonResponse({"stockAlert": alerts})


@login_required(login_url='signin')
def demand_forecast(request):
    if request.method == 'GET':
        demand = generate_demand_forecast()
        return JsonResponse(demand)


@login_required(login_url='signin')
def run_full_inventory_ai_engine(request):
    store = request.user.storeowneres
    forecast_data = generate_demand_forecast(store)
    stock_recommendations = generate_stock_recommendations(forecast_data,store)

    return JsonResponse({
        "total_products": len(stock_recommendations),
        "recommendations": stock_recommendations,
        "generated_at": str(timezone.now())
    }
)

