from rest_framework import serializers
from users.models import User
from users.validators import validate_special_character


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_special_character])
    confirm_password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'confirm_password')
   

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Password do not match"})
        return data

    def create(self, validated_data):
        # Remove confirm_password before creating the user
        validated_data.pop('confirm_password', None)
        user = User.objects.create_user(**validated_data)
        return user

