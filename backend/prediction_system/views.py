from prediction_system.models import WaterInfoModel,LstmTrainStatusModel
from prediction_system.serializers import WaterInfoModelSerializer, WaterInfoModelCreateUpdateSerializer, WaterInfoModelImportSerializer, ExportWaterInfoModelSerializer
from dvadmin.utils.viewset import CustomModelViewSet
from model.LstmModel import LstmModelTrainAll

from django.db import transaction
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status

import pandas as pd
import logging


# 涌水量信息视图类，用于管理WaterInfo表的所有信息
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

    # 一键删除的接口自定义, 删除涌水量信息表同时删除训练状态信息表
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
                # 删除涌水量信息表的所有数据
                water_deleted_count, _ = self.get_queryset().delete()
                # 附带删除训练状态中所有数据
                status_deleted_count, _ = LstmTrainStatusModel.objects.all().delete()
            return Response({'message': f'成功删除涌水量信息表 {water_deleted_count} 条数据, 训练状态信息表 {status_deleted_count} 条数据'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'detail': f'删除失败: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Lstm模型视图类，包含训练以及可视化，日志展示等功能
class LtsmModelViewSet(CustomModelViewSet):
    # 获取water_info中的所有数据
    waterData = WaterInfoModel.objects.all()
    status_data = LstmTrainStatusModel.objects.all()
    serializer_class = WaterInfoModelSerializer

    # Lstm模型训练函数
    @action(detail=False, methods=['post'], url_path='lstm-trainall')
    def Lstm_Train_All(self, request):
        try:
            # 获取查询集
            queryset = self.get_queryset()
            # 检查是否有数据
            if not queryset.exists():
                return Response({'detail': '数据不存在，请先导入数据'}, status=status.HTTP_400_BAD_REQUEST)

            # 将数据转化为pandas
            data = list(queryset.values())
            df = pd.DataFrame(data)

            # 调用模型进行训练
            # result为'success'表示所有模型训练成功,否则表示失败
            result = LstmModelTrainAll(df)

            # 根据返回结果判断训练是否成功
            if result == 'success':
                return Response({
                    'message': '模型训练成功',
                    'data_count': len(df),
                }, status=status.HTTP_200_OK)
            else:
                # 记录详细的错误日志
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"模型训练失败: {result}")

                return Response({
                    'detail': '模型训练失败',
                    'error': result
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"模型训练失败: {str(e)}", exc_info=True)

            return Response({
                'detail': '模型训练失败',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)