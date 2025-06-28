import { CrudOptions, AddReq, DelReq, EditReq, dict, CrudExpose, UserPageQuery, CreateCrudOptionsRet} from '@fast-crud/fast-crud';
import _ from 'lodash-es';
import * as api from './api';
import { request } from '/@/utils/service';
import {auth} from "/@/utils/authFunction";

//此处为crudOptions配置
export default function ({ crudExpose}: { crudExpose: CrudExpose}): CreateCrudOptionsRet {
    const pageRequest = async (query: any) => {
        return await api.GetList(query);
    };
    const editRequest = async ({ form, row }: EditReq) => {
        if (row.id) {
            form.id = row.id;
        }
        return await api.UpdateObj(form);
    };
    const delRequest = async ({ row }: DelReq) => {
        return await api.DelObj(row.id);
    };
    const addRequest = async ({ form }: AddReq) => {
        // 只传递模型名称到后端进行训练
        const { model_name } = form;
        return await api.AddObj(form);
    };

    const exportRequest = async (query: UserPageQuery) => {
        return await api.exportData(query)
    };

    return {
        crudOptions: {
            request: {
                pageRequest,
                addRequest,
                editRequest,
                delRequest,
            },
            actionbar: {
                buttons: {
                    export:{
                        // 注释编号:django-vue3-admin-crud210716:注意这个auth里面的值，最好是使用index.vue文件里面的name值并加上请求动作的单词
                        show: auth('BPTrainStatusModelViewSet:Export'),
                        text:"导出",//按钮文字
                        title:"导出",//鼠标停留显示的信息
                        click(){
                            return exportRequest(crudExpose.getSearchFormData())
                            // return exportRequest(crudExpose!.getSearchFormData())    // 注意这个crudExpose!.getSearchFormData()，一些低版本的环境是需要添加!的
                        }
                    },
                    add: {
                        show: auth('BPTrainStatusModelViewSet:Create'),
                    },
                    deleteAll: {
                        show: auth('BPTrainStatusModelViewSet:DeleteAll'), // 假设这里有对应的权限检查
                        text: "一键删除",
                        title: "删除所有BP模型信息数据",
                        click() {
                            return api.deleteAllWaterInfo().then(() => {
                                crudExpose.doRefresh(); // 删除成功后刷新列表
                            });
                        }
                    },
                }
            },
            rowHandle: {
                //固定右侧
                fixed: 'right',
                width: 200,
                buttons: {
                    view: {
                        type: 'text',
                        order: 1,
                        show: auth('BPTrainStatusModelViewSet:Retrieve')
                    },
                    edit: {
                        type: 'text',
                        order: 2,
                        show: auth('BPTrainStatusModelViewSet:Update')
                    },
                    copy: {
                        type: 'text',
                        order: 3,
                        show: auth('BPTrainStatusModelViewSet:Copy')
                    },
                    remove: {
                        type: 'text',
                        order: 4,
                        show: auth('BPTrainStatusModelViewSet:Delete')
                    },
                },
            },
            columns: {
                model_name: {
                    title: '模型名称',
                    type: 'string',
                    search: { show: true },
                    column: {
                        minWidth: 120,
                        sortable: 'custom',
                    },
                    form: {
                        rules: [{ required: true, message: '模型名称必填' }],
                        component: {
                            placeholder: '请输入模型名称',
                        },
                    },
                },
                training_time: {
                    title: '训练时间',
                    type: 'datetime',
                    search: { show: true },
                    column: {
                        minWidth: 120,
                        sortable: 'custom',
                    },
                    form: {
                        show: false, // 添加时不显示
                    },
                },
                train_status: {
                    title: '训练状态',
                    type: 'number',
                    search: { show: true },
                    column: {
                        minWidth: 120,
                        sortable: 'custom',
                        formatter: (row: any) => {
                            return row.train_status === 0 ? '训练失败' : '训练成功';
                        }
                    },
                    form: {
                        show: false, // 添加时不显示
                    },
                },
                train_rmse: {
                    title: '训练集 RMSE',
                    type: 'number',
                    search: { show: true },
                    column: {
                        minWidth: 120,
                        sortable: 'custom',
                    },
                    form: {
                        show: false, // 添加时不显示
                    },
                },
                test_rmse: {
                    title: '测试集 RMSE',
                    type: 'number',
                    search: { show: true },
                    column: {
                        minWidth: 120,
                        sortable: 'custom',
                    },
                    form: {
                        show: false, // 添加时不显示
                    },
                },

            },
        },
    };
}