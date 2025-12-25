"""
XFreeHD 插件 - AstrBot 插件
提供 XFreeHD 网站的视频和相册信息查询功能
"""
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from astrbot.api.message_components import Plain, Image, Video
from astrbot.core.message.message_event_result import MessageChain
import asyncio
import aiohttp
from typing import Optional
from PIL import Image as PILImage, ImageFilter
import io
import os
import re
import time


# XFreeHD 网站基础URL
BASE_URL = "https://xfreehd.com"
VIDEO_URL_TEMPLATE = f"{BASE_URL}/video/{{id}}"
ALBUM_URL_TEMPLATE = f"{BASE_URL}/album/{{id}}"

# 临时文件清理时间（秒）
TEMP_FILE_MAX_AGE = 3600  # 1小时


@register(
    "xfreehd",
    "YourName",
    "XFreeHD 视频和相册信息查询插件",
    "1.0.0"
)
class XFreeHDPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.client = None
        self.config = None
        self.temp_dir = os.path.join(os.path.dirname(__file__), "temp")
        
    async def initialize(self):
        """插件初始化"""
        try:
            from xfreehd_api import Client
            
            # 获取插件配置
            self.config = self.context.get_config(umo=None)
            
            # 创建客户端
            self.client = Client()
            
            # 清理旧的临时文件
            await self._cleanup_old_temp_files()
            
            logger.info("XFreeHD 插件初始化成功")
            
        except ImportError as e:
            logger.error(f"导入 xfreehd_api 失败: {e}")
            logger.error("请运行: pip install xfreehd_api")
        except Exception as e:
            logger.error(f"XFreeHD 插件初始化失败: {e}")
    
    async def terminate(self):
        """插件销毁"""
        if self.client:
            self.client = None
        
        # 清理所有临时文件
        await self._cleanup_all_temp_files()
        
        logger.info("XFreeHD 插件已终止")
    
    def _get_config(self, key: str, default=None):
        """获取配置值"""
        if self.config:
            return self.config.get(key, default)
        return default
    
    async def _cleanup_old_temp_files(self):
        """清理旧的临时文件（超过指定时间）"""
        try:
            if not os.path.exists(self.temp_dir):
                return
            
            current_time = time.time()
            cleaned_count = 0
            
            for filename in os.listdir(self.temp_dir):
                filepath = os.path.join(self.temp_dir, filename)
                if os.path.isfile(filepath):
                    file_age = current_time - os.path.getmtime(filepath)
                    if file_age > TEMP_FILE_MAX_AGE:
                        try:
                            os.remove(filepath)
                            cleaned_count += 1
                        except Exception as e:
                            logger.warning(f"删除临时文件失败 {filepath}: {e}")
            
            if cleaned_count > 0:
                logger.info(f"清理了 {cleaned_count} 个旧临时文件")
                
        except Exception as e:
            logger.error(f"清理旧临时文件失败: {e}")
    
    async def _cleanup_all_temp_files(self):
        """清理所有临时文件"""
        try:
            if not os.path.exists(self.temp_dir):
                return
            
            cleaned_count = 0
            for filename in os.listdir(self.temp_dir):
                filepath = os.path.join(self.temp_dir, filename)
                if os.path.isfile(filepath):
                    try:
                        os.remove(filepath)
                        cleaned_count += 1
                    except Exception as e:
                        logger.warning(f"删除临时文件失败 {filepath}: {e}")
            
            if cleaned_count > 0:
                logger.info(f"清理了 {cleaned_count} 个临时文件")
                
        except Exception as e:
            logger.error(f"清理临时文件失败: {e}")
    
    async def _cleanup_temp_file(self, filepath: str):
        """清理指定的临时文件"""
        try:
            if filepath and os.path.exists(filepath):
                os.remove(filepath)
                logger.debug(f"已清理临时文件: {filepath}")
        except Exception as e:
            logger.warning(f"清理临时文件失败 {filepath}: {e}")
    
    async def _download_and_blur_image(self, url: str) -> Optional[str]:
        """下载图片并应用打码效果"""
        try:
            blur_level = self._get_config("thumbnail_blur_level", 50)
            enable_thumbnail = self._get_config("enable_thumbnail", True)
            
            if not enable_thumbnail or blur_level == 0:
                return url  # 不打码，直接返回URL
            
            proxy_url = self._get_config("proxy_url", "")
            timeout = self._get_config("timeout", 30)
            
            async with aiohttp.ClientSession(trust_env=True) as session:
                kwargs = {"timeout": aiohttp.ClientTimeout(total=timeout)}
                if proxy_url:
                    kwargs["proxy"] = proxy_url
                
                async with session.get(url, **kwargs) as response:
                    if response.status == 200:
                        image_data = await response.read()
                        
                        # 使用 PIL 处理图片
                        img = PILImage.open(io.BytesIO(image_data))
                        
                        # 应用高斯模糊
                        if blur_level > 0:
                            # 将 0-100 映射到模糊半径 0-20
                            blur_radius = int(blur_level / 5)
                            if blur_radius > 0:
                                img = img.filter(ImageFilter.GaussianBlur(radius=blur_radius))
                        
                        # 保存到临时文件
                        temp_dir = os.path.join(os.path.dirname(__file__), "temp")
                        os.makedirs(temp_dir, exist_ok=True)
                        
                        temp_path = os.path.join(temp_dir, f"thumb_{hash(url)}.jpg")
                        img.save(temp_path, "JPEG", quality=85)
                        
                        return temp_path
            
            return url
            
        except Exception as e:
            logger.error(f"处理图片失败: {e}")
            return url
    
    def _format_message(self, text: str) -> str:
        """格式化消息，防止被 strip()"""
        return text + "\u200E"
    
    @filter.command("xfreehd_video_info", alias=["xfvi", "xf视频信息"])
    async def video_info(self, event: AstrMessageEvent, video_id: str = ""):
        """获取视频信息
        
        Args:
            video_id (string): 视频ID
        """
        if not video_id:
            yield event.plain_result(self._format_message("请提供视频ID\n用法: /xfreehd_video_info <视频ID>"))
            return
        
        try:
            if not self.client:
                yield event.plain_result(self._format_message("插件未正确初始化，请检查依赖安装"))
                return
            
            url = VIDEO_URL_TEMPLATE.format(id=video_id)
            video = self.client.get_video(url)
            
            # 构建消息
            info_lines = [
                f"📹 标题: {video.title}",
                f"👤 作者: {video.author}",
                f"👍 点赞: {video.likes}",
                f"👎 踩: {video.dislikes}",
                f"👁️ 观看: {video.views}",
                f"📅 发布: {video.publish_date}",
                f"⏱️ 时长: {video.length}",
                f"🎬 分类: {', '.join(video.categories)}",
                f"🏷️ 标签: {', '.join(video.tags)}",
                f"🔗 CDN数量: {len(video.cdn_urls)}"
            ]
            
            message = "\n".join(info_lines)
            
            # 获取封面图片
            thumbnail_url = video.thumbnail
            enable_thumbnail = self._get_config("enable_thumbnail", True)
            
            if enable_thumbnail and thumbnail_url:
                # 清理旧的临时文件
                await self._cleanup_old_temp_files()
                
                # 异步下载和处理图片
                thumbnail_path = await self._download_and_blur_image(thumbnail_url)
                
                if thumbnail_path and os.path.exists(thumbnail_path):
                    # 发送图片和文本
                    yield event.chain_result([
                        Image.fromFileSystem(thumbnail_path),
                        Plain(self._format_message(message))
                    ])
                    
                    # 发送完成后清理临时文件
                    await self._cleanup_temp_file(thumbnail_path)
                else:
                    yield event.plain_result(self._format_message(message))
            else:
                yield event.plain_result(self._format_message(message))
                
        except Exception as e:
            logger.error(f"获取视频信息失败: {e}")
            yield event.plain_result(self._format_message(f"获取视频信息失败: {str(e)}"))
    
    @filter.command("xfreehd_video_cdn", alias=["xfvc", "xf视频链接"])
    async def video_cdn(self, event: AstrMessageEvent, video_id: str = ""):
        """获取视频CDN链接
        
        Args:
            video_id (string): 视频ID
        """
        if not video_id:
            yield event.plain_result(self._format_message("请提供视频ID\n用法: /xfreehd_video_cdn <视频ID>"))
            return
        
        try:
            if not self.client:
                yield event.plain_result(self._format_message("插件未正确初始化"))
                return
            
            url = VIDEO_URL_TEMPLATE.format(id=video_id)
            video = self.client.get_video(url)
            cdn_urls = video.cdn_urls
            
            if not cdn_urls:
                yield event.plain_result(self._format_message("未找到可用的CDN链接"))
                return
            
            message = f"📹 视频标题: {video.title}\n\n"
            message += f"🔗 可用CDN链接:\n"
            
            for i, cdn_url in enumerate(cdn_urls, 1):
                quality = "HD" if i == len(cdn_urls) and len(cdn_urls) > 1 else "SD"
                message += f"{i}. [{quality}] {cdn_url}\n"
            
            yield event.plain_result(self._format_message(message))
            
        except Exception as e:
            logger.error(f"获取CDN链接失败: {e}")
            yield event.plain_result(self._format_message(f"获取CDN链接失败: {str(e)}"))
    
    @filter.command("xfreehd_album_info", alias=["xfai", "xf相册信息"])
    async def album_info(self, event: AstrMessageEvent, album_id: str = ""):
        """获取相册信息
        
        Args:
            album_id (string): 相册ID
        """
        if not album_id:
            yield event.plain_result(self._format_message("请提供相册ID\n用法: /xfreehd_album_info <相册ID>"))
            return
        
        try:
            if not self.client:
                yield event.plain_result(self._format_message("插件未正确初始化"))
                return
            
            url = ALBUM_URL_TEMPLATE.format(id=album_id)
            album = self.client.get_album(url)
            
            message = f"📁 相册标题: {album.title}\n"
            message += f"📄 总页数: {album.total_pages_count}\n"
            
            yield event.plain_result(self._format_message(message))
            
        except Exception as e:
            logger.error(f"获取相册信息失败: {e}")
            yield event.plain_result(self._format_message(f"获取相册信息失败: {str(e)}"))
    
    @filter.command("xfreehd_album_images", alias=["xfaim", "xf相册图片"])
    async def album_images(self, event: AstrMessageEvent, album_id: str = "", page: int = 1):
        """获取相册图片列表
        
        Args:
            album_id (string): 相册ID
            page (integer): 页码（默认为1）
        """
        if not album_id:
            yield event.plain_result(self._format_message("请提供相册ID\n用法: /xfreehd_album_images <相册ID> [页码]"))
            return
        
        try:
            if not self.client:
                yield event.plain_result(self._format_message("插件未正确初始化"))
                return
            
            url = ALBUM_URL_TEMPLATE.format(id=album_id)
            album = self.client.get_album(url)
            
            if page > album.total_pages_count:
                yield event.plain_result(self._format_message(f"页码超出范围，最大页数为 {album.total_pages_count}"))
                return
            
            images = album.get_images_by_page(page)
            max_results = self._get_config("max_results", 10)
            
            message = f"📁 相册: {album.title}\n"
            message += f"📄 第 {page}/{album.total_pages_count} 页\n\n"
            message += f"🖼️ 图片列表（显示前 {min(len(images), max_results)} 张）:\n\n"
            
            for i, img_url in enumerate(images[:max_results], 1):
                message += f"{i}. {img_url}\n"
            
            if len(images) > max_results:
                message += f"\n... 还有 {len(images) - max_results} 张图片"
            
            yield event.plain_result(self._format_message(message))
            
        except Exception as e:
            logger.error(f"获取相册图片失败: {e}")
            yield event.plain_result(self._format_message(f"获取相册图片失败: {str(e)}"))
    
    @filter.command("xfreehd_album_all_images", alias=["xfaai", "xf全部图片"])
    async def album_all_images(self, event: AstrMessageEvent, album_id: str = ""):
        """获取相册所有图片
        
        Args:
            album_id (string): 相册ID
        """
        if not album_id:
            yield event.plain_result(self._format_message("请提供相册ID\n用法: /xfreehd_album_all_images <相册ID>"))
            return
        
        try:
            if not self.client:
                yield event.plain_result(self._format_message("插件未正确初始化"))
                return
            
            url = ALBUM_URL_TEMPLATE.format(id=album_id)
            album = self.client.get_album(url)
            all_images = album.get_all_images()
            max_results = self._get_config("max_results", 10)
            
            message = f"📁 相册: {album.title}\n"
            message += f"📄 总页数: {album.total_pages_count}\n"
            message += f"🖼️ 总图片数: {len(all_images)}\n\n"
            message += f"图片列表（显示前 {min(len(all_images), max_results)} 张）:\n\n"
            
            for i, img_url in enumerate(all_images[:max_results], 1):
                message += f"{i}. {img_url}\n"
            
            if len(all_images) > max_results:
                message += f"\n... 还有 {len(all_images) - max_results} 张图片"
            
            yield event.plain_result(self._format_message(message))
            
        except Exception as e:
            logger.error(f"获取所有图片失败: {e}")
            yield event.plain_result(self._format_message(f"获取所有图片失败: {str(e)}"))
    
    @filter.command("xfreehd_help", alias=["xhelp", "xf帮助"])
    async def xfreehd_help(self, event: AstrMessageEvent):
        """显示插件帮助信息"""
        help_text = """
📚 XFreeHD 插件帮助

🔍 视频相关命令:
• /xfreehd_video_info <ID> - 获取视频详细信息
• /xfreehd_video_cdn <ID> - 获取视频CDN下载链接

📁 相册相关命令:
• /xfreehd_album_info <ID> - 获取相册信息
• /xfreehd_album_images <ID> [页码] - 获取指定页的图片列表
• /xfreehd_album_all_images <ID> - 获取相册所有图片

⚙️ 配置说明:
• 代理地址: 在插件配置中设置 proxy_url
• 封面打码: 在插件配置中设置 thumbnail_blur_level (0-100)
• 启用封面: 在插件配置中设置 enable_thumbnail

💡 提示:
• 所有命令都支持别名，如 /xfvi 等同于 /xfreehd_video_info
• 只需提供ID，无需输入完整URL
• 视频封面会根据配置自动打码
• 使用代理可以加速访问
        """
        
        yield event.plain_result(self._format_message(help_text.strip()))
