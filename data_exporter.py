import pandas as pd
import os
import datetime

class DataExporter:
    """将采集的信息导出到Excel表格的模块"""
    
    def __init__(self):
        self.default_excel_path = 'video_info.xlsx'
    
    def set_excel_path(self, path):
        """设置Excel文件路径"""
        self.default_excel_path = path
    
    def export_to_excel(self, video_info, excel_path=None):
        """将视频信息导出到Excel"""
        if not excel_path:
            excel_path = self.default_excel_path
        
        try:
            # 准备数据行
            data_row = {
                '视频标题': video_info.get('title', ''),
                '视频描述': video_info.get('description', ''),
                '标签': ', '.join(video_info.get('tags', [])),
                '文字稿': video_info.get('transcript', ''),
                '点赞数': video_info.get('stats', {}).get('likes', 0),
                '评论数': video_info.get('stats', {}).get('comments', 0),
                '收藏数': video_info.get('stats', {}).get('favorites', 0),
                '转发数': video_info.get('stats', {}).get('shares', 0),
                '账号名称': video_info.get('author', {}).get('name', ''),
                '抖音ID': video_info.get('author', {}).get('id', ''),
                '源链接': video_info.get('source_url', ''),
                '采集时间': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # 检查Excel文件是否已存在
            if os.path.exists(excel_path):
                # 读取现有Excel
                df_existing = pd.read_excel(excel_path)
                
                # 添加新行
                df_new = pd.DataFrame([data_row])
                df_updated = pd.concat([df_existing, df_new], ignore_index=True)
                
                # 保存更新后的Excel
                df_updated.to_excel(excel_path, index=False)
                print(f"视频信息已追加到Excel: {excel_path}")
            else:
                # 创建新的Excel
                df = pd.DataFrame([data_row])
                df.to_excel(excel_path, index=False)
                print(f"视频信息已导出到新Excel: {excel_path}")
            
            return True
            
        except Exception as e:
            print(f"导出到Excel时出错: {e}")
            return False