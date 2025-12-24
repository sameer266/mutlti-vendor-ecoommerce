from dashboard.models import Organization,ServiceBooking,Order

def global_context_processor(request):

    organization = Organization.objects.first()
    service_bookings_count = ServiceBooking.objects.filter(status='pending').count()
    peding_orders_count = Order.objects.filter(status='pending').count()
    return {
        'organization': organization,
        'total_service_bookings_pending': service_bookings_count,
        'total_pending_orders': peding_orders_count,
    }

