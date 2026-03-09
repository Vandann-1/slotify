from rest_framework import serializers
from .models import Plans , Subscription



class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plans  
        fields = '__all__'