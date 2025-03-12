import os
import pandas as pd
from utils.common import logger, create_directory

class ExcelExporter:
    def __init__(self, excel_path=None):
        """
        初始化Excel导出器
        
        Args:
            excel_path: Excel文件路径，如果不提供则使用默认路径
        """
        if excel_path:
            self.excel_path = excel_path
        else:
            # 默认保存在downloads目录下
            downloads_dir = 'downloads'
            create_directory(downloads_dir)
            self.excel_path = os.path.join(downloads_dir, 'video_data.xlsx')
    
    def set_excel_path(self, excel_path):
        """设置Excel文件路径"""
        self.excel_path = excel_path
    
    def export_single_item(self, data):
        """
        导出单个数据项到Excel
        
        Args:
            data: 要导出的数据字典
        
        Returns:
            是否成功导出
        """
        try:
            # 将数据转换为DataFrame
            df = pd.DataFrame([data])
            
            # 检查文件是否已存在
            if os.path.exists(self.excel_path):
                # 尝试加载现有的Excel文件
                try:
                    existing_df = pd.read_excel(self.excel_path)
                    # 合并现有数据和新数据
                    df = pd.concat([existing_df, df], ignore_index=True)
                except Exception as e:
                    logger.error(f"Error reading existing Excel file: {e}")
                    # 如果读取失败，使用新数据覆盖
            
            # 保存到Excel
            df.to_excel(self.excel_path, index=False)
            logger.info(f"Data exported to {self.excel_path}")
            return True
        except Exception as e:
            logger.error(f"Error exporting data to Excel: {e}")
            return False
    
    def export_batch(self, data_items):
        """
        批量导出数据项到Excel
        
        Args:
            data_items: 要导出的数据字典列表
        
        Returns:
            是否成功导出
        """
        if not data_items:
            logger.warning("No data items to export")
            return False
        
        try:
            # 将数据转换为DataFrame
            df = pd.DataFrame(data_items)
            
            # 检查文件是否已存在
            if os.path.exists(self.excel_path):
                # 尝试加载现有的Excel文件
                try:
                    existing_df = pd.read_excel(self.excel_path)
                    # 合并现有数据和新数据
                    df = pd.concat([existing_df, df], ignore_index=True)
                except Exception as e:
                    logger.error(f"Error reading existing Excel file: {e}")
                    # 如果读取失败，使用新数据覆盖
            
            # 保存到Excel
            df.to_excel(self.excel_path, index=False)
            logger.info(f"Batch data exported to {self.excel_path}")
            return True
        except Exception as e:
            logger.error(f"Error exporting batch data to Excel: {e}")
            return False
    
    def get_column_order(self):
        """获取标准的列顺序"""
        return [
            'title', 'description', 'tags', 'transcript',
            'likes', 'comments', 'favorites', 'shares',
            'author_name', 'author_id', 'source_url',
            'platform', 'video_id', 'local_video_path', 'local_audio_path'
        ]