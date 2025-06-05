from crud_demo.models import CrudDemoModel
from crud_demo.serializers import  CrudDemoModelSerializer, CrudDemoModelCreateUpdateSerializer, CrudDemoModelImportSerializer, ExportCrudDemoSerializer
from dvadmin.utils.viewset import CustomModelViewSet


class CrudDemoModelViewSet(CustomModelViewSet):
    """
    list:查询
    create:新增
    update:修改
    retrieve:单例
    destroy:删除
    """

    #注释编号:django-vue3-admin__views181311:码开始行
    # export_field_label = {
    #     "goods": "商品",
    #     "inventory": "库存量",
    #     "goods_price":"商品定价",
    #     "purchase_goods_date": "进货时间",
    # }

    # export_serializer_class = CrudDemoModelSerializer
    #注释编号:django-vue3-admin__views181311:代码结束行


    #注释编号:django-vue3-admin__views402916:代码开始行
    #功能说明:导入的配置
    import_field_dict = {
        "goods": "商品",
        "inventory": "库存量",
        "goods_price":"商品定价",
        "purchase_goods_date": {
            "title": '进货时间',
            "display":'purchase_goods_date',
            "type": "date"
        }
    }

    export_field_label = {
        "goods": "商品",
        "inventory": "库存量",
        'goods_price': "商品定价",
        "purchase_goods_date": {
            "title": '进货时间',
            "display":'purchase_goods_date',
            "type": "date"
        }
    }

    # 导入序列化器
    import_serializer_class = CrudDemoModelImportSerializer
    # 导出序列化器
    export_serializer_class = ExportCrudDemoSerializer

    #注释编号:django-vue3-admin__views402916:代码开始行

    queryset = CrudDemoModel.objects.all()
    serializer_class = CrudDemoModelSerializer
    create_serializer_class = CrudDemoModelCreateUpdateSerializer
    update_serializer_class = CrudDemoModelCreateUpdateSerializer