from prediction_system.models import WaterInfoModel
from prediction_system.serializers import WaterInfoModelSerializer, WaterInfoModelCreateUpdateSerializer, WaterInfoModelImportSerializer, ExportWaterInfoModelSerializer
from dvadmin.utils.viewset import CustomModelViewSet


class WaterInfoModelViewSet(CustomModelViewSet):
    """
    list:查询
    create:新增
    update:修改
    retrieve:单例
    destroy:删除
    """
    # 功能说明:导入的配置
    import_field_dict = {
        "date": {
            "title": '日期',
            "display":'date',
            "type": "date"
        },
        "longitude": "经度",
        "latitude": "纬度",
        "altitude": "高程",
        "rainfall": "日降雨量",
        "water_quantity": "涌水量"
    }

    # 导入序列化器
    import_serializer_class = WaterInfoModelImportSerializer

    export_field_label = {
        "date": {
            "title": '日期',
            "display": 'date',
            "type": "date"
        },
        "longitude": "经度",
        "latitude": "纬度",
        "altitude": "高程",
        "rainfall": "日降雨量",
        "water_quantity": "涌水量"
    }

    # 导入序列化器
    import_serializer_class = WaterInfoModelImportSerializer
    # 导出序列化器
    export_serializer_class = ExportWaterInfoModelSerializer

    queryset = WaterInfoModel.objects.all()
    serializer_class = WaterInfoModelSerializer
    create_serializer_class = WaterInfoModelCreateUpdateSerializer
    update_serializer_class = WaterInfoModelCreateUpdateSerializer