from prediction_system.models import WaterInfoModel
from prediction_system.serializers import WaterInfoModelSerializer, WaterInfoModelCreateUpdateSerializer, WaterInfoModelImportSerializer, ExportWaterInfoModelSerializer
from dvadmin.utils.viewset import CustomModelViewSet

from django.db import transaction
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status



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

    # 一键删除的接口自定义
    @action(detail=False, methods=['delete'], url_path='delete-all')
    def delete_all(self, request):
        """
        删除所有涌水量信息数据
        """
        # 添加权限检查（可选但推荐）
        if not request.user.has_perm('prediction_system.delete_waterinfomodel'):
            return Response({'detail': '权限不足'}, status=status.HTTP_403_FORBIDDEN)

        # 执行删除操作
        try:
            # 使用事务确保操作的原子性
            with transaction.atomic():
                deleted_count, _ = self.get_queryset().delete()
            return Response({'message': f'成功删除 {deleted_count} 条数据'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'detail': f'删除失败: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)