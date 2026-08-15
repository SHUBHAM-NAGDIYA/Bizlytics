from django.urls import path
from . import views 

urlpatterns = [
    path('', views.landing,name='landing'),
    path('signin/', views.signin, name='signin'),
    path('signout/', views.signout, name='signout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('registration/', views.registration, name='registration'),
    path('upload_sales/', views.upload_sales, name='upload_sales'),
    path('get_insights/', views.get_insights, name='get_insights'),
    path('forecast_demand/', views.forecast_demand, name='forcast_demand'),
    path('low_stock_alert/', views.low_stock_alert, name='lowStock_alert'),
    path('demand_forecast/', views.generate_demand_forecast, name ='demand_forecast' ),
    path('run_full_inventory_ai_engine/', views.run_full_inventory_ai_engine, name='run_full_inventory_ai_engine')
    
]