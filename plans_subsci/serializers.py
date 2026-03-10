from rest_framework import serializers
from .models import Plans , Subscription



class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plans  
        fields = '__all__'
        
        
class SubscriptionSerializer(serializers.ModelSerializer):
    
    plan_name = serializers.CharField(source='plan.name',read_only=True)
    member_limit = serializers.IntegerField(source='plan.member_limit', read_only=True)
    class Meta:
        model = Subscription
        fields = ['id', 'plan', 'plan_name', 'member_limit', 'tenant', 'razorpay_subscription_id', 'start_date', 'end_date', 'is_active']        