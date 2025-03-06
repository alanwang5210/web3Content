import json
import os
from pathlib import Path
from urllib.parse import urlparse

import requests

from cms_token import TokenCache
from config_load import CONFIG

token_cache = TokenCache()


def post_article(article):
    """
    Posts an article to the backend API.
    """
    url = CONFIG['CMS_HOST'] + CONFIG['NEW_ARTICLE_PATH']

    token = token_cache.get_token()

    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + token
    }

    response = requests.post(url, headers=headers, data=json.dumps(article))
    print(response.text)


def check_article_title(title):
    """
    check the article title is exist
    """

    url = CONFIG['CMS_HOST'] + CONFIG['CHECK_ARTICLE_TITLE_PATH']

    token = token_cache.get_token()

    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + token
    }
    try:

        response = requests.get(url, headers=headers, params={'title': title})
        return not response.json().get('data')
    except Exception as e:
        print(f"文章名称重复校验失败: {e}")
        return False


def upload(download_url, resource_type):
    """
    check the article title is exist
    """
    if resource_type == 'image':
        url = CONFIG['CMS_HOST'] + CONFIG['IMAGE_UPLOAD_PATH']
        file_name = get_url_file_name(download_url, resource_type)
    elif resource_type == 'media':
        url = CONFIG['CMS_HOST'] + CONFIG['MEDIA_UPLOAD_PATH']
        file_name = get_url_file_name(download_url, resource_type)
    elif resource_type == 'file':
        url = CONFIG['CMS_HOST'] + CONFIG['FILE_UPLOAD_PATH']
        file_name = get_url_file_name(download_url, resource_type)
    elif resource_type == 'audio':
        url = CONFIG['CMS_HOST'] + CONFIG['AUDIO_UPLOAD_PATH']
        file_name = get_url_file_name(download_url, resource_type)
    else:
        return False

    token = token_cache.get_token()

    headers = {
        'Authorization': 'Bearer ' + token
    }

    try:
        # 以流式方式从 URL 获取文件内容
        response = requests.get(download_url, stream=True)
        response.raise_for_status()  # 检查请求是否成功
    except Exception as e:
        print(f"文件上传失败:{download_url}, {e}")
        return False

    # 读取内容并上传，确保用正确的文件名和 MIME 类型
    files = {
        'file': (file_name, response.content)
    }

    try:
        response = requests.post(url, headers=headers, files=files)
        url = response.json().get('url')
        if url:
            return url
        else:
            print('文件上传失败: ' + download_url)
        return False
    except Exception as e:
        print('文件上传失败: ' + download_url)
        print(f"文件上传失败: {e}")
        return False


# 默认扩展名配置
DEFAULT_EXTENSIONS = {
    'image': 'jpg',
    'media': 'mp4',
    'file': 'txt',
    'audio': 'mp3',
    'document': 'pdf',
    'video': 'mp4',
    'data': 'json',
    'html': 'html',
    'css': 'css',
    'js': 'js'
}


def get_url_extension(url, default_extension='html'):
    """获取URL中的文件后缀名，如果没有后缀则返回默认值

    Args:
        url (str): 需要解析的URL
        default_extension (str): 默认的文件后缀，不包含点号，默认为'html'

    Returns:
        str: 文件后缀（不包含点号）。如果URL没有后缀，则返回default_extension
    """
    # 解析URL
    parsed_url = urlparse(url)

    # 获取路径部分
    path = parsed_url.path

    # 如果路径为空或以斜杠结尾，返回默认后缀
    if not path or path.endswith('/'):
        return default_extension

    # 移除查询参数和锚点后的路径部分
    clean_path = path.split('?')[0].split('#')[0]

    # 获取文件扩展名
    extension = os.path.splitext(clean_path)[1]

    # 如果有后缀，返回不带点号的后缀；否则返回默认后缀
    return extension[1:] if extension else default_extension


def get_url_file_name(url, resource_type):
    """从URL中提取文件名，如果文件没有后缀，则根据资源类型设置默认后缀

    Args:
        url (str): 需要解析的URL
        resource_type (str): 资源类型，用于确定默认后缀，可选值包括'image', 'media', 'file', 'audio'等

    Returns:
        str: 提取的文件名（包含后缀）

    Examples:
        >>> get_url_file_name('http://example.com/images/photo.jpg', 'image')
        'photo.jpg'
        >>> get_url_file_name('http://example.com/download/document', 'document')
        'document.pdf'
        >>> get_url_file_name('http://example.com/music/', 'audio')
        'default.mp3'
    """
    # 解析URL
    parsed_url = urlparse(url)

    # 获取路径部分
    path = parsed_url.path

    # 如果路径为空或以斜杠结尾，使用默认文件名
    if not path or path.endswith('/'):
        return f"default.{DEFAULT_EXTENSIONS.get(resource_type, 'txt')}"

    # 移除查询参数和锚点
    clean_path = path.split('?')[0].split('#')[0]

    # 使用Path获取文件名
    filename = Path(clean_path).name

    filename.replace('/', '_').replace('*', '_').replace('?', '_')

    # 检查文件是否有扩展名
    if '.' in filename and not filename.endswith('.'):
        return filename

    # 如果没有扩展名，添加默认扩展名
    default_ext = DEFAULT_EXTENSIONS.get(resource_type, 'txt')
    return f"{filename}.{default_ext}"
