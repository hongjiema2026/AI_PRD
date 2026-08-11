#!/usr/bin/env python3
"""
登录处理模块
职责：处理需要认证的页面，支持多种登录方式
"""

import logging
import re
import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class AuthHandler:
    """认证处理器"""

    def __init__(self, session=None):
        self.session = session or requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        })

    def login(self, url, username=None, password=None, captcha=None, cookie=None):
        """
        执行登录

        支持方式：
        1. Cookie 直接注入（最可靠）
        2. 账号密码表单提交
        3. 账号密码+验证码
        """
        if cookie:
            return self._login_with_cookie(cookie)

        if username and password:
            return self._login_with_form(url, username, password, captcha)

        return False

    def _login_with_cookie(self, cookie_string):
        """使用 Cookie 字符串登录"""
        try:
            # 解析 Cookie 字符串
            cookies = {}
            for item in cookie_string.split(";"):
                item = item.strip()
                if "=" in item:
                    k, v = item.split("=", 1)
                    cookies[k.strip()] = v.strip()

            # 设置到 session
            self.session.cookies.update(cookies)
            logger.info(f"  [Auth] Cookie 已设置 ({len(cookies)} 个)")
            return True

        except Exception as e:
            logger.info(f"  [Auth] Cookie 解析失败: {e}")
            return False

    def _login_with_form(self, url, username, password, captcha=None):
        """使用表单登录"""
        try:
            # 获取登录页面
            logger.info(f"  [Auth] 获取登录页面: {url}")
            resp = self.session.get(url, timeout=30)
            soup = BeautifulSoup(resp.text, "html.parser")

            # 查找登录表单
            login_form = self._find_login_form(soup)
            if not login_form:
                logger.info("  [Auth] 未找到登录表单，尝试直接 POST")
                return self._try_direct_login(url, username, password, captcha)

            # 构建表单数据
            form_data = {}
            action = login_form.get("action", url)
            action_url = urljoin(url, action)

            # 提取所有 input 字段
            for input_tag in login_form.find_all("input"):
                name = input_tag.get("name")
                input_type = input_tag.get("type", "text")
                value = input_tag.get("value", "")

                if not name:
                    continue

                # 判断字段类型
                if input_type == "password":
                    form_data[name] = password
                elif self._is_username_field(name, input_type):
                    form_data[name] = username
                elif input_type == "hidden":
                    form_data[name] = value
                elif captcha and self._is_captcha_field(name):
                    form_data[name] = captcha
                elif input_type in ["text", "email", "tel"]:
                    # 可能是用户名或其他字段
                    if "user" in name.lower() or "name" in name.lower() or "mail" in name.lower() or "phone" in name.lower():
                        form_data[name] = username
                    elif captcha and ("captcha" in name.lower() or "verify" in name.lower() or "code" in name.lower()):
                        form_data[name] = captcha

            logger.info(f"  [Auth] 表单字段: {list(form_data.keys())}")

            # 提交表单
            method = login_form.get("method", "post").lower()
            if method == "post":
                submit_resp = self.session.post(action_url, data=form_data, timeout=30)
            else:
                submit_resp = self.session.get(action_url, params=form_data, timeout=30)

            # 检查登录结果
            if self._check_login_success(submit_resp):
                logger.info("  [Auth] 登录成功")
                return True
            else:
                logger.warning("  [Auth] 登录可能失败，响应状态: %s", submit_resp.status_code)
                # 即使状态码不是 200，Cookie 可能已经设置
                return len(self.session.cookies) > 0

        except Exception as e:
            logger.info(f"  [Auth] 登录异常: {e}")
            return False

    def _find_login_form(self, soup):
        """查找登录表单"""
        # 策略1：找包含密码输入框的表单
        for form in soup.find_all("form"):
            if form.find("input", {"type": "password"}):
                return form

        # 策略2：找 action 包含 login/signin 的表单
        for form in soup.find_all("form"):
            action = form.get("action", "").lower()
            if any(kw in action for kw in ["login", "signin", "auth", "sign_in"]):
                return form

        return None

    def _is_username_field(self, name, input_type):
        """判断是否为用户名字段"""
        username_keywords = ["user", "name", "email", "mail", "phone", "mobile", "account", "id"]
        return any(kw in name.lower() for kw in username_keywords) and input_type != "password"

    def _is_captcha_field(self, name):
        """判断是否为验证码字段"""
        captcha_keywords = ["captcha", "verify", "verification", "code", "vcode"]
        return any(kw in name.lower() for kw in captcha_keywords)

    def _try_direct_login(self, url, username, password, captcha=None):
        """尝试直接 POST 到常见登录接口"""
        common_endpoints = ["/login", "/signin", "/auth", "/api/login", "/api/auth"]
        base = urljoin(url, "/")

        data = {
            "username": username,
            "password": password,
        }
        if captcha:
            data["captcha"] = captcha

        for endpoint in common_endpoints:
            try:
                login_url = urljoin(base, endpoint)
                resp = self.session.post(login_url, data=data, timeout=30)
                if self._check_login_success(resp):
                    logger.info(f"  [Auth] 直接登录成功: {login_url}")
                    return True
            except Exception:
                continue

        logger.info("  [Auth] 直接登录尝试失败")
        return False

    def _check_login_success(self, response):
        """检查登录是否成功"""
        text_lower = response.text.lower()

        # 策略1：检查是否被重定向回登录页
        url_lower = response.url.lower()
        if "login" in url_lower or "signin" in url_lower:
            # 确认页面中仍有密码输入框，才判定为失败
            soup = BeautifulSoup(response.text, "html.parser")
            if soup.find("input", {"type": "password"}):
                return False

        # 策略2：检查响应中是否有明确的登录错误提示
        login_error_indicators = [
            "invalid username", "invalid password", "wrong password",
            "incorrect password", "login failed", "authentication failed",
            "密码错误", "用户名或密码错误", "登录失败", "认证失败",
        ]
        for indicator in login_error_indicators:
            if indicator in text_lower:
                return False

        # 策略3：检查是否有会话级 cookie
        if len(self.session.cookies) > 0:
            for cookie in self.session.cookies:
                cookie_name = cookie.name.lower()
                if any(kw in cookie_name for kw in ["session", "token", "auth", "sid", "userid"]):
                    return True

        # 策略4：结合状态码判断
        if response.status_code in [301, 302]:
            # 重定向到非登录页通常表示成功
            location = response.headers.get("Location", "")
            if location and "login" not in location.lower() and "signin" not in location.lower():
                return True

        # 200 状态码单独不能判定成功，需配合其他信号
        return False

    def detect_login_type(self, url):
        """检测页面登录类型，返回详细信息供 Planner 使用"""
        try:
            resp = self.session.get(url, timeout=30)
            soup = BeautifulSoup(resp.text, "html.parser")

            result = {
                "has_login_form": False,
                "has_password_field": False,
                "has_captcha": False,
                "captcha_image_url": None,
                "form_action": None,
                "username_field_name": None,
                "password_field_name": None,
            }

            login_form = self._find_login_form(soup)
            if login_form:
                result["has_login_form"] = True
                result["form_action"] = login_form.get("action")

                for input_tag in login_form.find_all("input"):
                    input_type = input_tag.get("type", "text")
                    name = input_tag.get("name", "")

                    if input_type == "password":
                        result["has_password_field"] = True
                        result["password_field_name"] = name

                    if self._is_username_field(name, input_type):
                        result["username_field_name"] = name

                    if self._is_captcha_field(name):
                        result["has_captcha"] = True

                # 查找验证码图片
                captcha_img = soup.find("img", {
                    "src": re.compile(r"captcha|verify", re.I)
                })
                if captcha_img:
                    result["has_captcha"] = True
                    result["captcha_image_url"] = urljoin(url, captcha_img.get("src", ""))

            return result

        except Exception as e:
            return {"error": str(e)}
