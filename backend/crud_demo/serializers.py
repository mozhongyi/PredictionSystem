#backend/crud_demo/serializers.py

from crud_demo.models import CrudDemoModel
from dvadmin.utils.serializers import CustomModelSerializer


class CrudDemoModelSerializer(CustomModelSerializer):
    """
    序列化器
    """
#这里是进行了序列化模型及所有的字段
    class Meta:
        model = CrudDemoModel
        fields = "__all__"

#这里是创建/更新时的列化器
class CrudDemoModelCreateUpdateSerializer(CustomModelSerializer):
    """
    创建/更新时的列化器
    """

    class Meta:
        model = CrudDemoModel
        fields = '__all__'