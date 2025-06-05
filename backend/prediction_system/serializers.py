from prediction_system.models import WaterInfoModel
from dvadmin.utils.serializers import CustomModelSerializer


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

#导入时用到的列化器
class WaterInfoModelImportSerializer(CustomModelSerializer):
    """
    WaterInfoModel导入时的列化器
    """

    class Meta:
        model = WaterInfoModel
        fields = '__all__'

#导出时用到的列化器
class ExportWaterInfoModelSerializer(CustomModelSerializer):
    """
    WaterInfoModel导入时的列化器
    """

    class Meta:
        model = WaterInfoModel
        fields = '__all__'