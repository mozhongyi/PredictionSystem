import { CrudOptions, AddReq, DelReq, EditReq, dict, CrudExpose, UserPageQuery, CreateCrudOptionsRet} from '@fast-crud/fast-crud';
import _ from 'lodash-es';
import * as api from './api';
import { request } from '/@/utils/service';
import {auth} from "/@/utils/authFunction";

// 导入训练单个点的接口
import { trainSinglePoint,getLog } from './api';


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
                        show: auth('LtsmModelViewSet:Export'),
                        text:"导出",//按钮文字
                        title:"导出",//鼠标停留显示的信息
                        click(){
                            return exportRequest(crudExpose.getSearchFormData())
                            // return exportRequest(crudExpose!.getSearchFormData())    // 注意这个crudExpose!.getSearchFormData()，一些低版本的环境是需要添加!的
                        }
                    },
                    add: {
                        show: auth('LtsmModelViewSet:Create'),
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
                        show: auth('LtsmModelViewSet:Retrieve')
                    },
                    edit: {
                        type: 'text',
                        order: 2,
                        show: auth('LtsmModelViewSet:Update')
                    },
                    copy: {
                        type: 'text',
                        order: 3,
                        show: auth('LtsmModelViewSet:Copy')
                    },
                    remove: {
                        type: 'text',
                        order: 4,
                        show: auth('LtsmModelViewSet:Delete')
                    },
                    // 添加“训练”按钮
                    train: {
                        type: 'text',
                        order: 5,
                        show: auth('LtsmModelViewSet:Train'),
                        text: '训练',
                        click: async ({ row }) => {
                            try {
                                const { longitude, latitude, altitude } = row;
                                const response = await trainSinglePoint({ longitude, latitude, altitude });
                                if (response.data.message === '模型训练成功') {
                                    // 更新训练状态为成功
                                    row.trainStatus = "已训练";
                                    // 刷新列表
                                    crudExpose.doRefresh();
                                }
                            } catch (error) {
                                // 更新训练状态为失败
                                row.trainStatus = 2;
                                // 刷新列表
                                crudExpose.doRefresh();
                                // 处理训练失败的情况
                                console.error('训练失败:', error);
                            }
                        }
                    },
                    trainLog:{
                        type: 'text',
                        order: 6,
                        show: auth('LtsmModelViewSet:GetLog'),
                        text: '训练日志',
                        click: async ({ row }) =>{
                            try{
                                const { longitude, latitude, altitude } = row;
                                const response = await getLog( longitude, latitude, altitude );
                                console.log('response 对象:',response)
                                console.log('response.status = ',response.status)
                                if (response.status === '200')
                                {
                                    const logContent = response.data;
                                    // 创建一个文本框元素
                                    const textarea = document.createElement('textarea');
                                    textarea.value = logContent;
                                    textarea.style.width = '80%';
                                    textarea.style.height = '300px';
                                    textarea.style.position = 'fixed';
                                    textarea.style.top = '50%';
                                    textarea.style.left = '50%';
                                    textarea.style.transform = 'translate(-50%, -50%)';
                                    textarea.style.zIndex = '9999';
                                    textarea.style.border = '1px solid #ccc';
                                    textarea.style.padding = '10px';
                                    textarea.style.backgroundColor = 'white';
                                    textarea.readOnly = true;

                                    // 创建一个关闭按钮
                                    const closeButton = document.createElement('button');
                                    closeButton.textContent = '关闭';
                                    closeButton.style.position = 'fixed';
                                    closeButton.style.top = 'calc(50% + 150px)';
                                    closeButton.style.left = '50%';
                                    closeButton.style.transform = 'translateX(-50%)';
                                    closeButton.style.zIndex = '10000';
                                    closeButton.addEventListener('click', () => {
                                        document.body.removeChild(textarea);
                                        document.body.removeChild(closeButton);
                                    });

                                    // 将文本框和关闭按钮添加到页面中
                                    document.body.appendChild(textarea);
                                    document.body.appendChild(closeButton);
                                }
                                else
                                {
                                    console.error('获取训练日志失败:', response.data.detail);
                                }


                            } catch (error) {
                                console.error('获取训练日志失败:', error);
                            }
                        }
                    }
                },
            },
            columns: {
                longitude: {
                    title: '经度',
                    type: 'number',
                    search: { show: true },
                    column: {
                        minWidth: 120,
                        sortable: 'custom',
                    },
                    form: {
                        rules: [{ required: true, message: '经度必填' }],
                        component: {
                            placeholder: '请输入经度',
                            // 控制小数位数为3位
                            step: 0.001,
                        },
                    },
                },

                latitude: {
                    title: '纬度',
                    type: 'number',
                    search: { show: true },
                    column: {
                        minWidth: 120,
                        sortable: 'custom',
                    },
                    form: {
                        rules: [{ required: true, message: '纬度必填' }],
                        component: {
                            placeholder: '请输入纬度',
                            step: 0.001,
                        },
                    },
                },
                altitude: {
                    title: '高程',
                    type: 'number',
                    search: { show: false },
                    column: {
                        minWidth: 120,
                        sortable: 'custom',
                    },
                    form: {
                        rules: [{ required: true, message: '高程必填' }],
                        component: {
                            placeholder: '请输入高程',
                            step: 0.001,
                        },
                    },
                },
                trainStatus: {
                    title: '训练状态',
                    type: 'text',
                    search: {
                        show: false
                    },
                    column: {
                        minWidth: 120,
                        sortable: 'custom',
                    },
                },
            },
        },
    };
}