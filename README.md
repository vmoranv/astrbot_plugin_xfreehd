# AstrBot XFreeHD 插件

一个功能强大的 AstrBot 插件，用于查询 XFreeHD 网站的视频和相册信息。

## 功能特性

- 📹 **视频信息查询** - 获取视频的详细信息，包括标题、作者、点赞数、观看数等
- 🔗 **CDN链接获取** - 获取视频的CDN下载链接（支持HD/SD质量）
- 📁 **相册信息查询** - 获取相册的基本信息和总页数
- 🖼️ **相册图片列表** - 获取相册中指定页或所有页的图片链接
- 🎨 **封面打码** - 支持对视频封面进行不同程度的打码处理
- 🌐 **代理支持** - 支持通过代理服务器访问
- ⚙️ **灵活配置** - 提供丰富的配置选项

## 配置

在 AstrBot 的插件配置页面中，可以配置以下选项：

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `proxy_url` | string | "" | 代理服务器地址（例如：http://127.0.0.1:7890） |
| `thumbnail_blur_level` | integer | 50 | 视频封面打码程度（0-100，0为不打码，100为完全打码） |
| `enable_thumbnail` | boolean | true | 是否返回视频封面图片 |
| `max_results` | integer | 10 | 最大返回结果数量 |
| `timeout` | integer | 30 | 请求超时时间（秒） |

## 命令列表

### 视频相关命令

#### `/xfreehd_video_info <ID>` 或 `/xfvi <ID>`
获取视频的详细信息。

**示例：**
```
/xfreehd_video_info 12345
```

**返回信息包括：**
- 标题
- 作者
- 点赞数
- 踩数
- 观看数
- 发布日期
- 时长
- 分类
- 标签
- CDN数量
- 封面图片（根据配置决定是否显示）

#### `/xfreehd_video_cdn <ID>` 或 `/xfvc <ID>`
获取视频的CDN下载链接。

**示例：**
```
/xfreehd_video_cdn 12345
```

### 相册相关命令

#### `/xfreehd_album_info <ID>` 或 `/xfai <ID>`
获取相册的基本信息。

**示例：**
```
/xfreehd_album_info 12345
```

#### `/xfreehd_album_images <ID> [页码]` 或 `/xfaim <ID> [页码]`
获取相册指定页的图片列表。

**示例：**
```
/xfreehd_album_images 12345 1
```

#### `/xfreehd_album_all_images <ID>` 或 `/xfaai <ID>`
获取相册所有页的图片列表。

**示例：**
```
/xfreehd_album_all_images 12345
```

### 帮助命令

#### `/xfreehd_help` 或 `/xhelp` 或 `/xf帮助`
显示插件帮助信息。

## 使用示例

### 查询视频信息

```
用户: /xfreehd_video_info 12345

机器人: 📹 标题: 示例视频标题
       👤 作者: 示例作者
       👍 点赞: 100
       👎 踩: 5
       👁️ 观看: 1000
       📅 发布: 2024-01-01
       ⏱️ 时长: 10:30
       🎬 分类: 分类1, 分类2
       🏷️ 标签: 标签1, 标签2
       🔗 CDN数量: 2
       
       [封面图片]
```

### 获取CDN链接

```
用户: /xfreehd_video_cdn 12345

机器人: 📹 视频标题: 示例视频标题
       
       🔗 可用CDN链接:
       1. [SD] https://cdn1.xfreehd.com/video/12345_sd.mp4
       2. [HD] https://cdn1.xfreehd.com/video/12345_hd.mp4
```

### 查询相册信息

```
用户: /xfreehd_album_info 12345

机器人: 📁 相册标题: 示例相册
       📄 总页数: 5
```

### 获取相册图片

```
用户: /xfreehd_album_images 12345 1

机器人: 📁 相册: 示例相册
       📄 第 1/5 页
       
       🖼️ 图片列表（显示前 10 张）:
       
       1. https://xfreehd.com/image/001.jpg
       2. https://xfreehd.com/image/002.jpg
       3. https://xfreehd.com/image/003.jpg
       ...
```

## 注意事项

1. **依赖安装**：确保已安装 `xfreehd_api` 库及其依赖
2. **网络访问**：插件需要访问 XFreeHD 网站，请确保网络连接正常
3. **代理设置**：如果访问速度慢，建议配置代理服务器
4. **封面打码**：根据需要调整打码程度，0为不打码，100为完全打码
5. **消息格式**：所有消息末尾会添加零宽字符 `\u200E` 以防止被 `strip()` 处理
6. **ID输入**：所有命令只需提供ID，无需输入完整URL

## 技术细节

### 插件架构

- 基于 AstrBot 插件系统开发
- 使用 `xfreehd_api` 库进行数据获取
- 支持异步操作，提高性能
- 使用 PIL 进行图片处理（打码）

### 消息组件

插件使用以下消息组件：
- `Plain` - 纯文本消息
- `Image` - 图片消息（封面）

### 配置管理

插件配置通过 `_conf_schema.json` 定义，支持：
- 字段类型验证
- 默认值设置
- 范围限制（如打码程度 0-100）

## 故障排查

### 插件无法加载

1. 检查是否安装了 `xfreehd_api` 库
2. 查看日志文件获取详细错误信息
3. 确认 Python 版本兼容性（建议 3.10+）

### 无法获取视频信息

1. 检查网络连接
2. 尝试配置代理服务器
3. 确认 ID 格式正确（只需数字ID）
4. 查看日志获取详细错误信息

### 封面图片不显示

1. 检查 `enable_thumbnail` 配置是否为 `true`
2. 检查 `thumbnail_blur_level` 配置
3. 确认临时目录有写入权限

## 免责声明

本插件仅供学习和研究使用。请遵守当地法律法规，不要用于任何非法用途。插件作者不对使用本插件造成的任何后果负责。

## 致谢

- [AstrBot](https://github.com/Soulter/AstrBot) - 强大的聊天机器人框架
- [xfreehd_api](https://github.com/yourname/xfreehd_api) - XFreeHD API 库