from prediction_system.models import WaterInfoModel,LstmTrainStatusModel
from dvadmin.utils.serializers import CustomModelSerializer
from rest_framework import serializers
from django.db import transaction


class WaterInfoModelSerializer(CustomModelSerializer):
    """
    序列化器
    """
#这里是进行了序列化模型及所有的字段
    class Meta:
        model = WaterInfoModel
        fields = "__all__"

#这里是创建/更新时的列化器
class WaterInfoModelCreateUpdateSerializer(CustomModelSerializer):
    """
    创建/更新时的列化器
    """

    class Meta:
        model = WaterInfoModel
        fields = '__all__'

    def create(self, validated_data):
        if isinstance(validated_data, list):  # 处理批量导入
            with transaction.atomic():
                instances = []
                for data in validated_data:
                    longitude = data.get('longitude')
                    latitude = data.get('latitude')
                    altitude = data.get('altitude')
                    # 检查 LstmTrainStatusModel 中是否已经存在该经纬度和高程的记录
                    lstm_train_status, created = LstmTrainStatusModel.objects.get_or_create(
                        longitude=longitude,
                        latitude=latitude,
                        altitude=altitude,
                        defaults={'is_train': 0}
                    )
                    instance = WaterInfoModel.objects.create(**data)
                    instances.append(instance)
                return instances
        else:  # 处理单条导入
            longitude = validated_data.get('longitude')
            latitude = validated_data.get('latitude')
            altitude = validated_data.get('altitude')
            # 检查 LstmTrainStatusModel 中是否已经存在该经纬度和高程的记录
            lstm_train_status, created = LstmTrainStatusModel.objects.get_or_create(
                longitude=longitude,
                latitude=latitude,
                altitude=altitude,
                defaults={'is_train': 0}
            )
            return WaterInfoModel.objects.create(**validated_data)

#导入时用到的列化器
class WaterInfoModelImportSerializer(CustomModelSerializer):
    """
    WaterInfoModel导入时的列化器
    """

    class Meta:
        model = WaterInfoModel
        fields = '__all__'

    def create(self, validated_data):
        if isinstance(validated_data, list):  # 处理批量导入
            with transaction.atomic():
                instances = []
                for data in validated_data:
                    longitude = data.get('longitude')
                    latitude = data.get('latitude')
                    altitude = data.get('altitude')
                    # 检查 LstmTrainStatusModel 中是否已经存在该经纬度和高程的记录
                    lstm_train_status, created = LstmTrainStatusModel.objects.get_or_create(
                        longitude=longitude,
                        latitude=latitude,
                        altitude=altitude,
                        defaults={'is_train': 0}
                    )
                    instance = WaterInfoModel.objects.create(**data)
                    instances.append(instance)
                return instances
        else:  # 处理单条导入
            longitude = validated_data.get('longitude')
            latitude = validated_data.get('latitude')
            altitude = validated_data.get('altitude')
            # 检查 LstmTrainStatusModel 中是否已经存在该经纬度和高程的记录
            lstm_train_status, created = LstmTrainStatusModel.objects.get_or_create(
                longitude=longitude,
                latitude=latitude,
                altitude=altitude,
                defaults={'is_train': 0}
            )
            return WaterInfoModel.objects.create(**validated_data)

#导出时用到的列化器
class ExportWaterInfoModelSerializer(CustomModelSerializer):
    """
    WaterInfoModel导入时的列化器
    """

    class Meta:
        model = WaterInfoModel
        fields = '__all__'

class LstmTrainStatusModelSerializer(CustomModelSerializer):
    """
    LSTM训练状态数据的序列化器
    """

    # get_<field>_display() 方法,自动将0/1转换为未训练/已训练
    trainStatus = serializers.CharField(source='get_is_train_display', read_only=True)

    class Meta:
        model = LstmTrainStatusModel
        fields = "__all__"

class LstmTrainStatusModelCreateUpdateSerializer(CustomModelSerializer):
    """
    创建/更新LSTM训练状态时的序列化器
    """
    class Meta:
        model = LstmTrainStatusModel
        fields = '__all__'
        read_only_fields = ("id",)  # 创建后不可修改ID