import { request,downloadFile } from '/@/utils/service';
import { PageQuery, AddReq, DelReq, EditReq, InfoReq } from '@fast-crud/fast-crud';

export const apiPrefix = '/api/BPTrainStatusModelViewSet/';

export function GetList(query: PageQuery) {
    return request({
        url: apiPrefix,                 // 请求地址：/api/WaterInfoModelViewSet/
        method: 'get',                  // GET 请求
        params: query,                  // 查询参数（分页、过滤等）
    });
}
export function GetObj(id: InfoReq) {
    return request({
        url: apiPrefix + id,            // 请求地址：/api/WaterInfoModelViewSet/{id}
        method: 'get',                  // GET 请求
    });
}

export function AddObj(obj: AddReq) {
    return request({
        url: apiPrefix,                 // 请求地址：/api/WaterInfoModelViewSet/
        method: 'post',                 // POST 请求
        data: obj,                      // 要添加的对象数据
    });
}

export function UpdateObj(obj: EditReq) {
    return request({
        url: apiPrefix + obj.id + '/',      // 请求地址：/api/WaterInfoModelViewSet/{id}/
        method: 'put',                      // PUT 请求
        data: obj,                          // 更新后的对象数据
    });
}

export function DelObj(id: DelReq) {
    return request({
        url: apiPrefix + id + '/',          // 请求地址：/api/WaterInfoModelViewSet/{id}/
        method: 'delete',                   // DELETE 请求
        data: { id },                       // 要删除的对象ID（可选，有些API需要）
    });
}

export function exportData(params:any){
    // 使用专门的下载文件函数
    return downloadFile({
        url: apiPrefix + 'export_data/',        // 导出地址：/api/WaterInfoModelViewSet/export_data/
        params: params,                         // 导出参数（过滤条件等）
        method: 'get'                           // GET 请求
    })
}

// 一键删除的请求函数，用于调用后端一键删除接口
export function deleteAllWaterInfo() {
    return request({
        url: apiPrefix + 'delete-all/',
        method: 'delete',
    });
}

// 获取日志的接口调用函数
export function getLog(modelName:string) {
    return request({
        url: apiPrefix + 'get-log/',
        method: 'get',
        params: { modelName }
    });
}

// 获取Bp可视化图片的接口调用函数
export function get_bp_image(modelName:string ) {
    return request({
        url: apiPrefix + 'get_bp_image/',
        method: 'get',
        params: modelName,
        responseType: 'blob' // 因为返回的是图片二进制数据，所以设置响应类型为 blob
    });
}
