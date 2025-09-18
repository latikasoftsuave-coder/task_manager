from rest_framework import serializers
from activity.models import Task, ActivityLog
from categories.serializers import CategorySerializer
from tags.serializers import TagSerializer
from categories.models import Category
from tags.models import Tag

class TaskSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    tag_names = serializers.StringRelatedField(source='tags', many=True, read_only=True)

    title = serializers.CharField(required=True)
    status = serializers.ChoiceField(choices=Task.STATUS_CHOICES, required=True)
    priority = serializers.ChoiceField(choices=Task.PRIORITY_CHOICES, required=True)

    class Meta:
        model = Task
        exclude = ('category', 'tags', 'user', 'created_at', 'updated_at')
        read_only_fields = ('id', 'user', 'created_at', 'updated_at')

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        request = self.context.get("request")
        if request and request.method == "PUT":
            # enforce full replacement → missing fields reset to default/null
            model = self.Meta.model
            for field in model._meta.get_fields():
                field_name = field.name
                if (
                        field_name not in validated_data
                        and field_name not in self.Meta.read_only_fields
                        and not field.many_to_many
                        and not field.one_to_many
                ):
                    model_field = model._meta.get_field(field_name)
                    if model_field.has_default():
                        validated_data[field_name] = model_field.get_default()
                    elif getattr(model_field, "null", False):
                        validated_data[field_name] = None
                    elif getattr(model_field, "blank", False):
                        validated_data[field_name] = ""
        return super().update(instance, validated_data)


class ActivityLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivityLog
        fields = '__all__'

class TaskCategorySerializer(serializers.Serializer):
    category_id = serializers.UUIDField()

    def validate_category_id(self, value):
        if not Category.objects.filter(id=value).exists():
            raise serializers.ValidationError("Category not found.")
        return value


class TaskTagSerializer(serializers.Serializer):
    tags = serializers.ListField(
        child=serializers.UUIDField(), allow_empty=False
    )

    def validate_tags(self, value):
        missing = [tag_id for tag_id in value if not Tag.objects.filter(id=tag_id).exists()]
        if missing:
            raise serializers.ValidationError(f"Tags not found: {missing}")
        return value