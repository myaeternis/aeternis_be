"""
API Views for Orders.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import Order
from .serializers import (
    OrderInputSerializer, 
    OrderSerializer,
    CalculateTotalInputSerializer
)
from .services import OrderService, PricingService


class CalculateTotalView(APIView):
    """
    POST /api/orders/calculate/
    
    Calculate order totals without creating an order.
    Used to validate frontend calculations.
    """
    
    def post(self, request):
        serializer = CalculateTotalInputSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {'error': 'Invalid data', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            pricing = PricingService()
            totals = pricing.calculate_order_total(serializer.validated_data['profiles'])
            
            # Convert Decimals to floats for JSON
            response_data = {
                'plansCost': float(totals['plans_cost']),
                'plaquesCost': float(totals['plaques_cost']),
                'addonsCost': float(totals['addons_cost']),
                'extensionsCost': float(totals['extensions_cost']),
                'subtotal': float(totals['subtotal']),
                'copyDiscount': float(totals['copy_discount']),
                'bundleDiscount': float(totals['bundle_discount']),
                'bundleDiscountRate': float(totals['bundle_discount_rate']),
                'shippingCost': float(totals['shipping_cost']),
                'total': float(totals['total']),
                'profileCount': totals['profile_count'],
                'completeProfileCount': totals['complete_profile_count'],
            }
            
            return Response(response_data)
            
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class CreateOrderView(APIView):
    """
    POST /api/orders/
    
    Create a new order from cart data.
    Returns order details and Stripe checkout URL.
    """
    
    def post(self, request):
        serializer = OrderInputSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {'error': 'Invalid data', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            service = OrderService()
            order = service.create_order(
                order_data=serializer.validated_data,
                request=request
            )
            
            order_serializer = OrderSerializer(order)
            return Response(order_serializer.data, status=status.HTTP_201_CREATED)
            
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class OrderDetailView(APIView):
    """
    GET /api/orders/<order_id>/
    
    Get order details by ID or order number.
    """
    
    def get(self, request, order_id):
        try:
            # Try to find by UUID first, then by order number
            try:
                order = Order.objects.get(pk=order_id)
            except (Order.DoesNotExist, ValueError):
                order = Order.objects.get(order_number=order_id)
            
            serializer = OrderSerializer(order)
            return Response(serializer.data)
            
        except Order.DoesNotExist:
            return Response(
                {'error': 'Order not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class OrderByEmailView(APIView):
    """
    GET /api/orders/by-email/?email=<email>
    
    Get orders by customer email.
    """
    
    def get(self, request):
        email = request.query_params.get('email')
        
        if not email:
            return Response(
                {'error': 'Email parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        orders = Order.objects.filter(customer_email=email)
        
        from .serializers import OrderSummarySerializer
        serializer = OrderSummarySerializer(orders, many=True)
        return Response(serializer.data)
