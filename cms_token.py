import base64
import json
import threading
import time

import requests
from gmssl import sm2

from config_load import CONFIG


def encrypt_data(data, public_key):
    """
    SM2加密数据
    :param data: 要加密的数据
    :param public_key: 公钥（16进制字符串格式）
    :return: 加密后的数据
    """

    # SM2加密
    sm2_crypt = sm2.CryptSM2(public_key=public_key, private_key=None, mode=1)
    enc_data = sm2_crypt.encrypt(data.encode())

    # 把加密后的数据转为16进制字符串
    enc_hex = enc_data.hex()

    # 拼接 '04'（表示非压缩格式的公钥/加密数据）
    enc_with_prefix = '04' + enc_hex

    # 转为 Base64 编码
    enc_base64 = base64.b64encode(bytes.fromhex(enc_with_prefix)).decode()

    return enc_base64


class TokenCache:
    def __init__(self):
        self.token = None
        self.refresh_token = None
        self.expiry_time = 0

    def get_token(self):
        current_time = time.time()
        if self.token and current_time < self.expiry_time - CONFIG['TOKEN_REFRESH_BUFFER']:
            return self.token

        if self.token and current_time >= self.expiry_time - CONFIG['TOKEN_REFRESH_BUFFER']:
            print("Token nearing expiry, attempting to refresh")
            return self.refresh_token_request()

        print("Fetching new token")
        return self.fetch_new_token()

    def fetch_new_token(self):
        payload = json.dumps({
            "username": CONFIG['USERNAME'],
            #"password": CONFIG['PASSWORD']
            "password": encrypt_data(CONFIG['PASSWORD'], get_public_key())
        })
        headers = {'Content-Type': 'application/json'}

        response = requests.post(CONFIG['CMS_HOST'] + CONFIG['LOGIN_PATH'], headers=headers, data=payload)
        if response.status_code == 200:
            data = response.json().get('result', {})
            if data:
                self.refresh_self(data)
                print("New token fetched: " + self.token)
                return self.token
            else:
                print("Failed to fetch token", response.text)
                return None
        else:
            print("Failed to fetch token", response.text)
            return None

    def refresh_token_request(self):
        payload = json.dumps({"refreshToken": self.refresh_token})
        headers = {'Content-Type': 'application/json'}

        response = requests.post(CONFIG['CMS_HOST'] + CONFIG['REFRESH_PATH'], headers=headers, data=payload)
        if response.status_code == 200:
            data = response.json().get('result', {})
            if data:
                self.refresh_self(data)
                print("Token refreshed: " + self.token)
                return self.token
            else:
                print("Failed to refresh token", response.text)
                return None
        else:
            print("Failed to refresh token", response.text)
            return self.fetch_new_token()

    def refresh_self(self, data):
        self.token = data.get('accessToken')
        self.refresh_token = data.get('refreshToken')
        expires_in = data.get('expiresIn', CONFIG['DEFAULT_EXPIRES_IN'])
        self.expiry_time = time.time() + expires_in

    def start_token_refresh_loop(self):
        while True:
            self.get_token()
            sleep_time = max(self.expiry_time - time.time() - CONFIG['TOKEN_REFRESH_BUFFER'], 1)
            print(f"Sleeping for {sleep_time} seconds")
            time.sleep(sleep_time)


def start_token_refresh_in_thread():
    refresh_thread = threading.Thread(target=token_cache.start_token_refresh_loop, daemon=True)
    refresh_thread.start()


def get_public_key():
    """
    Posts an article to the backend API.
    """
    url = CONFIG['CMS_HOST'] + CONFIG['PUBLIC-KEY_PATH']

    response = requests.get(url)
    return response.text


# 启动 token 刷新循环
token_cache = TokenCache()
start_token_refresh_in_thread()
