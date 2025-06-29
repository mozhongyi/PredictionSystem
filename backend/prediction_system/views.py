import os
import time

from prediction_system.models import WaterInfoModel,LstmTrainStatusModel,WaterLevelModel,WaterQualityModel,BPTrainStatusModel
from prediction_system.serializers import WaterInfoModelSerializer, WaterInfoModelCreateUpdateSerializer, WaterInfoModelImportSerializer, ExportWaterInfoModelSerializer
from prediction_system.serializers import LstmTrainStatusModelSerializer,LstmTrainStatusModelCreateUpdateSerializer
from prediction_system.serializers import WaterLevelModelSerializer,WaterLevelModelCreateUpdateSerializer,WaterLevelModelImportSerializer,ExportWaterLevelModelSerializer
from prediction_system.serializers import WaterQualityModelSerializer,WaterQualityModelCreateUpdateSerializer,WaterQualityModelImportSerializer,ExportWaterQualityModelSerializer
from prediction_system.serializers import BPTrainStatusModelSerializer,BPTrainStatusModelCreateUpdateSerializer
from dvadmin.utils.viewset import CustomModelViewSet
from model.LstmModel import LstmModelTrainSingle
from model.BPModel import BPTrain,PredictWaterQuality

from django.db import transaction
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
import chardet

from django.http.response import HttpResponse

import pandas as pd
import logging


# 涌水量信息视图类，用于管理WaterInfo表的所有信息
from rest_framework.status import HTTP_201_CREATED


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
    serializer_class = LstmTrainStatusModelSerializer
    queryset = LstmTrainStatusModel.objects.all()
    update_serializer_class = LstmTrainStatusModelCreateUpdateSerializer

    # Lstm模型训练单个点函数
    @action(detail=False, methods=['post'], url_path='lstm-trainsingle')
    def Lstm_Train_Single(self, request):
        # 获取water_info中的所有数据
        waterData = WaterInfoModel.objects.all()
        try:
            # 获取前端传入的经纬度和高程信息
            longitude = request.data.get('longitude')
            latitude = request.data.get('latitude')
            altitude = request.data.get('altitude')

            # 验证必要参数
            if not all([longitude, latitude, altitude]):
                return Response({
                    'detail': '缺少必要参数：经度、纬度和高程',
                }, status=status.HTTP_400_BAD_REQUEST)

            # 从waterData中筛选匹配经纬度和高程的数据
            filtered_data = waterData.filter(
                longitude=longitude,
                latitude=latitude,
                altitude=altitude
            )

            # 获取或创建对应的训练状态记录
            status_instance, created = LstmTrainStatusModel.objects.get_or_create(
                longitude=longitude,
                latitude=latitude,
                altitude=altitude,
                defaults={'is_train': 0}  # 默认未训练状态
            )

            # 检查是否有匹配的数据
            if not filtered_data.exists():
                return Response({
                    'detail': f'未找到经度={longitude}, 纬度={latitude}, 高程={altitude} 的数据'
                }, status=status.HTTP_404_NOT_FOUND)

            # 将筛选的数据转换为DataFrame
            data = list(filtered_data.values())
            df = pd.DataFrame(data)

            # 调用模型进行训练
            # result为'success'表示所有模型训练成功,否则表示失败
            result = LstmModelTrainSingle(df)

            # 使用事务确保更新原子性
            with transaction.atomic():
                if result == 'success':
                    # 方案：使用更新序列化器处理数据更新
                    update_data = {'is_train': 1}
                    serializer = self.update_serializer_class(
                        status_instance,
                        data=update_data,
                        partial=True
                    )
                    serializer.is_valid(raise_exception=True)
                    updated_instance = serializer.save()

                    return Response({
                        'message': '模型训练成功',
                        'data_count': len(df),
                    }, status=status.HTTP_200_OK)
                else:
                    # 训练失败时更新状态
                    update_data = {'is_train': 2}
                    serializer = self.update_serializer_class(
                        status_instance,
                        data=update_data,
                        partial=True
                    )
                    serializer.is_valid(raise_exception=True)
                    serializer.save()

                    return Response({
                        'detail': '模型训练失败',
                        'error': result,
                        'status': 2
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            # 异常处理中更新状态
            with transaction.atomic():
                if 'status_instance' in locals():
                    update_data = {'is_train': 2}
                    serializer = self.update_serializer_class(
                        status_instance,
                        data=update_data,
                        partial=True
                    )
                    serializer.is_valid(raise_exception=False)  # 异常时不严格验证
                    serializer.save()

            return Response({
                'detail': '模型训练失败',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # 获取日志的接口（改进版）
    @action(detail=False, methods=['get'], url_path='get-log')
    def get_log(self, request):
        # 获取前端传入的经纬度和高程信息
        longitude = request.query_params.get('longitude')
        latitude = request.query_params.get('latitude')
        altitude = request.query_params.get('altitude')

        # 验证必要参数
        if not all([longitude, latitude, altitude]):
            return Response({
                'detail': '缺少必要参数：经度、纬度和高程',
            }, status=status.HTTP_400_BAD_REQUEST)

        # 组装目标日志路径（使用更规范的文件名格式）
        log_path = f'lstm_logs/({longitude},{latitude},{altitude})training.log'

        # 检查日志文件是否存在
        if os.path.exists(log_path):
            try:
                # 方案1：自动检测文件编码（推荐）
                with open(log_path, 'rb') as f:
                    raw_data = f.read(2048)  # 读取前2KB用于检测编码
                    encoding = chardet.detect(raw_data)['encoding'] or 'utf-8'

                # 使用检测到的编码读取文件
                with open(log_path, 'r', encoding=encoding) as file:
                    log_content = file.read()

                return Response({
                    'status': '200',
                    'data': log_content
                }, status=status.HTTP_200_OK)

            except Exception as e:
                return Response({
                    'status': '500'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        else:
            return Response({
                'status': '404'
            }, status=status.HTTP_404_NOT_FOUND)

    # 获取模型可视化图片的接口
    @action(detail=False, methods=['get'], url_path='get_lstm_image')
    def get_visualization_image(self, request):
        # 获取前端传入的经纬度和高程信息
        longitude = request.query_params.get('longitude')
        latitude = request.query_params.get('latitude')
        altitude = request.query_params.get('altitude')

        # 验证必要参数
        if not all([longitude, latitude, altitude]):
            return Response({
                'detail': '缺少必要参数：经度、纬度和高程',
            }, status=status.HTTP_400_BAD_REQUEST)

        # 组装目标图片路径（使用更规范的文件名格式）
        image_path = f'lstm_images/({longitude},{latitude},{altitude})真实值vs预测值.png'

        # 检查图片文件是否存在
        if os.path.exists(image_path):
            try:
                # 读取图片文件
                with open(image_path, 'rb') as file:
                    image_data = file.read()

                # 响应图片数据给前端
                return HttpResponse(image_data, content_type='image/jpg')
                #return Response(image_data, status=status.HTTP_200_OK, content_type='image/png')

            except Exception as e:
                return Response({
                    'detail': f'读取图片失败: {str(e)}',
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        else:
            return Response({
                'detail': '未找到对应的可视化图片',
            }, status=status.HTTP_404_NOT_FOUND)


# 水位信息视图类，用于管理水位信息
class WaterLevelModelViewset(CustomModelViewSet):
    # 功能说明:导入的配置
    import_field_dict = {
        "date": {
            "title": '日期',
            "display": 'date',
            "type": "date"
        },
        "longitude": "经度",
        "latitude": "纬度",
        "altitude": "高程",
        "water_level": "水位"
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
        "water_level": "涌水量"
    }

    # 导入序列化器
    import_serializer_class = WaterLevelModelImportSerializer
    # 导出序列化器
    export_serializer_class = ExportWaterLevelModelSerializer

    queryset = WaterLevelModel.objects.all()
    serializer_class = WaterLevelModelSerializer
    create_serializer_class = WaterLevelModelCreateUpdateSerializer
    update_serializer_class = WaterLevelModelCreateUpdateSerializer

    # 一键删除的接口自定义, 删除涌水量信息表同时删除训练状态信息表
    @action(detail=False, methods=['delete'], url_path='delete-all')
    def delete_all(self, request):
        """
        删除所有涌水量信息数据
        """
        # 添加权限检查（可选但推荐）
        if not request.user.has_perm('prediction_system.delete_waterlevelmodel'):
            return Response({'detail': '权限不足'}, status=status.HTTP_403_FORBIDDEN)

        # 执行删除操作
        try:
            # 使用事务确保操作的原子性
            with transaction.atomic():
                # 删除涌水量信息表的所有数据
                water_deleted_count, _ = self.get_queryset().delete()
            return Response({'message': f'成功删除水位信息表 {water_deleted_count} 条数据'},
                            status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'detail': f'删除失败: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# 水质信息视图类，用于管理水质信息
class WaterQualityModelViewset(CustomModelViewSet):
    # 功能说明:导入的配置
    import_field_dict = {
        "longitude": "经度",
        "latitude": "纬度",
        "altitude": "高程",
        "stratigraphic_lithology": "地层岩性",
        "sulfate_ion_concentration": "硫酸根离子浓度",
        "carbonate_ion_concentration": "碳酸根离子浓度",
        "total_dissolved_solids": "溶解性总固体",
        "ph": "pH",
        "calcium_magnesium_ratio": "钙镁比值",
        "eight_h": "8-H",
        "eight_o": "8-O"
    }

    export_field_label = {
        "longitude": "经度",
        "latitude": "纬度",
        "altitude": "高程",
        "stratigraphic_lithology": "地层岩性",
        "sulfate_ion_concentration": "硫酸根离子浓度",
        "carbonate_ion_concentration": "碳酸根离子浓度",
        "total_dissolved_solids": "溶解性总固体",
        "ph": "pH",
        "calcium_magnesium_ratio": "钙镁比值",
        "eight_h": "8-H",
        "eight_o": "8-O"
    }

    # 导入序列化器
    import_serializer_class = WaterQualityModelImportSerializer
    # 导出序列化器
    export_serializer_class = ExportWaterQualityModelSerializer

    queryset = WaterQualityModel.objects.all()
    serializer_class = WaterQualityModelSerializer
    create_serializer_class = WaterQualityModelCreateUpdateSerializer
    update_serializer_class = WaterQualityModelCreateUpdateSerializer

    # 一键删除的接口自定义
    @action(detail=False, methods=['delete'], url_path='delete-all')
    def delete_all(self, request):
        """
        删除所有水质点信息数据
        """
        # 添加权限检查（可选但推荐）
        if not request.user.has_perm('prediction_system.delete_waterqualitypointmodel'):
            return Response({'detail': '权限不足'}, status=status.HTTP_403_FORBIDDEN)

        # 执行删除操作
        try:
            # 使用事务确保操作的原子性
            with transaction.atomic():
                # 删除水质点信息表的所有数据
                deleted_count, _ = self.get_queryset().delete()
            return Response({'message': f'成功删除水质点信息表 {deleted_count} 条数据'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'detail': f'删除失败: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# BP 模型训练状态视图类，用于管理 BP 模型训练状态信息
class BPTrainStatusModelViewSet(CustomModelViewSet):
    serializer_class = BPTrainStatusModelSerializer
    queryset = BPTrainStatusModel.objects.all()
    create_serializer_class = BPTrainStatusModelCreateUpdateSerializer
    update_serializer_class = BPTrainStatusModelCreateUpdateSerializer

    # 一键删除的接口自定义
    @action(detail=False, methods=['delete'], url_path='delete-all')
    def delete_all(self, request):
        """
        删除所有水质点信息数据
        """

        # 执行删除操作
        try:
            # 使用事务确保操作的原子性
            with transaction.atomic():
                # 删除水质点信息表的所有数据
                deleted_count, _ = self.get_queryset().delete()
            return Response({'message': f'成功删除BP训练状态信息表 {deleted_count} 条数据'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'detail': f'删除失败: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # 重写添加方法
    def create(self, request):
        # 仅获取模型名称（假设前端只传递 model_name）
        model_name = request.data.get('model_name')
        if not model_name:
            return Response({'error': '模型名称不能为空'}, status=400)

        # 获取 waterInfo 和 waterLevel 的数据
        try:
            water_info_data = WaterInfoModel.objects.all()
            water_info_df = pd.DataFrame(list(water_info_data.values()))
            # 转换需要的列
            water_info_df['longitude'] = water_info_df['longitude'].astype(float)
            water_info_df['latitude'] = water_info_df['latitude'].astype(float)
            water_info_df['altitude'] = water_info_df['altitude'].astype(float)
            water_info_df['rainfall'] = water_info_df['rainfall'].astype(float)
            water_info_df['water_quantity'] = water_info_df['water_quantity'].astype(float)

            water_level_data = WaterLevelModel.objects.all()
            water_level_df = pd.DataFrame(list(water_level_data.values()))
            # 转换需要的列
            water_level_df['longitude'] = water_level_df['longitude'].astype(float)
            water_level_df['latitude'] = water_level_df['latitude'].astype(float)
            water_level_df['altitude'] = water_level_df['altitude'].astype(float)
            water_level_df['water_level'] = water_level_df['water_level'].astype(float)
        except Exception as e:
            return Response({'error': f'获取数据失败: {str(e)}'}, status=500)

        # 调用训练函数
        try:
            train_time, train_rmse, test_rmse, train_status = BPTrain(model_name, water_info_df, water_level_df)
        except Exception as e:
            return Response({'error': f'模型训练失败: {str(e)}'}, status=500)

        # 构造完整数据
        data = {
            'model_name': model_name,
            'training_time': train_time,
            'train_rmse': train_rmse,
            'test_rmse': test_rmse,
            'train_status': train_status
        }

        # 使用序列化器验证并保存
        serializer = self.get_serializer(data=data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        serializer.save()

        return Response({'message': '训练成功'}, status=HTTP_201_CREATED)

    # 获取日志的接口（改进版）
    @action(detail=False, methods=['get'], url_path='get-log')
    def get_log(self, request):
        # 获取前端传入的经纬度和高程信息
        modelName = request.query_params.get('modelName')


        # 验证必要参数
        if not all([modelName]):
            return Response({
                'detail': '缺少必要参数：模型名称',
            }, status=status.HTTP_400_BAD_REQUEST)

        # 组装目标日志路径（使用更规范的文件名格式）
        log_path = f'bp_logs/{modelName}training.log'

        # 检查日志文件是否存在
        if os.path.exists(log_path):
            try:
                # 方案1：自动检测文件编码（推荐）
                with open(log_path, 'rb') as f:
                    raw_data = f.read(2048)  # 读取前2KB用于检测编码
                    encoding = chardet.detect(raw_data)['encoding'] or 'utf-8'

                # 使用检测到的编码读取文件
                with open(log_path, 'r', encoding=encoding) as file:
                    log_content = file.read()

                return Response({
                    'status': '200',
                    'data': log_content
                }, status=status.HTTP_200_OK)

            except Exception as e:
                return Response({
                    'status': '500'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        else:
            return Response({
                'status': '404'
            }, status=status.HTTP_404_NOT_FOUND)

    # 获取模型可视化图片的接口
    @action(detail=False, methods=['get'], url_path='get_bp_image')
    def get_visualization_image(self, request):
        # 获取前端传入的经纬度和高程信息
        modelName = request.query_params.get('model_name')

        # 验证必要参数
        if not all([modelName]):
            return Response({
                'detail': '缺少必要参数：模型名称',
            }, status=status.HTTP_400_BAD_REQUEST)

        # 组装目标图片路径（使用更规范的文件名格式）
        image_path = f'bp_images/{modelName}真实值vs预测值.png'

        # 检查图片文件是否存在
        if os.path.exists(image_path):
            try:
                # 读取图片文件
                with open(image_path, 'rb') as file:
                    image_data = file.read()

                # 响应图片数据给前端
                return HttpResponse(image_data, content_type='image/jpg')
                # return Response(image_data, status=status.HTTP_200_OK, content_type='image/png')

            except Exception as e:
                return Response({
                    'detail': f'读取图片失败: {str(e)}',
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        else:
            return Response({
                'detail': '未找到对应的可视化图片',
            }, status=status.HTTP_404_NOT_FOUND)

    # 用户预测接口
    @action(detail=False, methods=['post'], url_path='predict-water-quality')
    def predict_water_quality(self, request):
        # 获取前端传入的经度、纬度、高程和模型名称
        user_lon = request.data.get('longitude')
        user_lat = request.data.get('latitude')
        user_elev = request.data.get('altitude')
        model_name = request.data.get('model_name')

        # 验证必要参数
        if not all([user_lon, user_lat, user_elev, model_name]):
            return Response({
                'detail': '缺少必要参数：经度、纬度、高程和模型名称',
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # 获取 waterInfo 和 waterLevel 的数据
            water_info_data = WaterInfoModel.objects.all()
            water_info_df = pd.DataFrame(list(water_info_data.values()))
            # 转换需要的列
            water_info_df['longitude'] = water_info_df['longitude'].astype(float)
            water_info_df['latitude'] = water_info_df['latitude'].astype(float)
            water_info_df['altitude'] = water_info_df['altitude'].astype(float)
            water_info_df['rainfall'] = water_info_df['rainfall'].astype(float)
            water_info_df['water_quantity'] = water_info_df['water_quantity'].astype(float)

            water_level_data = WaterLevelModel.objects.all()
            water_level_df = pd.DataFrame(list(water_level_data.values()))
            # 转换需要的列
            water_level_df['longitude'] = water_level_df['longitude'].astype(float)
            water_level_df['latitude'] = water_level_df['latitude'].astype(float)
            water_level_df['altitude'] = water_level_df['altitude'].astype(float)
            water_level_df['water_level'] = water_level_df['water_level'].astype(float)

            # 调用预测函数
            prediction = PredictWaterQuality(user_lon, user_lat, user_elev, water_info_df, water_level_df, model_name)

            prediction = round(prediction,3)
            prediction = prediction / 2.5

            return Response({
                'prediction': prediction
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'detail': f'预测失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)