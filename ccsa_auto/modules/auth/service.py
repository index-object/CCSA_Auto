import sys
import os
import requests  # 添加requests库用于发送HTTP请求
import threading

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath('.'))

from refactored_code.auth_module import AuthModule
from refactored_code.config import Config as RefactoredConfig

from ccsa_auto.core.database import SessionLocal
from ccsa_auto.core.models import User
from ccsa_auto.utils.password import hash_password
from ccsa_auto.utils.jwt import create_access_token

# 用于防止配置修改冲突的锁
_config_lock = threading.Lock()

class AuthService:
    """认证服务"""
    
    @staticmethod
    def authenticate_external(username, password):
        """外部平台认证"""
        try:
            # 创建认证模块实例
            auth_module = AuthModule()
            
            # 使用锁保护配置修改，防止多个线程同时修改配置
            with _config_lock:
                # 修改配置为用户提供的账号密码
                original_username = RefactoredConfig.LOGIN_DATA['username']
                original_password = RefactoredConfig.LOGIN_DATA['password']
                
                try:
                    RefactoredConfig.LOGIN_DATA['username'] = username
                    RefactoredConfig.LOGIN_DATA['password'] = password
                    
                    # 尝试登录
                    success = auth_module.login()
                    
                    if success:
                        # 获取用户信息
                        user_info = AuthService.get_user_info(auth_module)
                        return True, user_info, auth_module.access_token
                    else:
                        return False, None, None
                finally:
                    # 恢复原始配置
                    RefactoredConfig.LOGIN_DATA['username'] = original_username
                    RefactoredConfig.LOGIN_DATA['password'] = original_password
                
        except Exception as e:
            print(f"外部平台认证失败: {e}")
            return False, None, None
    
    @staticmethod
    def get_user_info(auth_module):
        """获取用户信息"""
        try:
            # 调用API获取用户信息
            headers = {
                'accept': 'application/json, text/plain, */*',
                'authorization': f'Bearer {auth_module.access_token}',
                'clientid': RefactoredConfig.CLIENT_ID,
                'content-language': 'zh_CN',
            }
            response = requests.get(
                f"{RefactoredConfig.BASE_URL}/system/app/userExtend/v2/getUserInfo",
                headers=headers
            )
            response_data = response.json()
            
            if response.status_code == 200 and response_data.get('code') == 200:
                data = response_data.get('data', {})
                return {
                    'username': data.get('nickName', ''),
                    'company_name': data.get('companyName', '')
                }
            else:
                print(f"获取用户信息失败: {response_data.get('msg', '未知错误')}")
                return {
                    'username': '',
                    'company_name': ''
                }
        except Exception as e:
            print(f"调用用户信息API时发生异常: {e}")
            return {
                'username': '',
                'company_name': ''
            }
    
    @staticmethod
    def auto_register(username, password, user_info=None):
        """自动注册用户
        Args:
            username: 用户名
            password: 密码
            user_info: 可选的用户信息，如果已从外部API获取则传入以避免重复调用
        """
        db = SessionLocal()
        try:
            # 检查用户是否已存在
            existing_user = db.query(User).filter_by(username=username).first()
            
            # 如果用户已存在，更新公司信息（如果提供了user_info）
            if existing_user:
                if user_info and user_info.get('company_name'):
                    existing_user.company_name = user_info.get('company_name')
                    db.commit()
                    db.refresh(existing_user)
                return existing_user
            
            # 如果用户不存在且没有提供user_info，则需要获取用户信息
            if not user_info:
                auth_success, user_info, _ = AuthService.authenticate_external(username, password)
                if not auth_success:
                    return None
            
            # 创建新用户
            new_user = User(
                username=username,
                password=hash_password(password),
                external_username=username,
                external_password=hash_password(password),
                company_name=user_info.get('company_name', ''),
                status=0
            )
            
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            return new_user
        finally:
            db.close()
    
    @staticmethod
    def login(username, password):
        """用户登录"""
        # 外部平台认证
        auth_success, user_info, external_token = AuthService.authenticate_external(username, password)
        if not auth_success:
            return False, None, "外部平台认证失败"
        
        # 自动注册或获取用户，传入已获取的user_info避免重复认证
        user = AuthService.auto_register(username, password, user_info)
        if not user:
            return False, None, "用户注册失败"
        
        # 检查用户状态
        if user.status == 1:
            return False, None, "账号已被封禁"
        
        # 创建访问令牌
        access_token = create_access_token({"sub": str(user.id)})
        
        # 使用从外部API获取的最新用户信息（特别是公司名称）
        # 注意：user_info是从外部API获取的，包含最新的nickName和companyName
        return True, {
            'access_token': access_token,
            'external_token': external_token,
            'user': {
                'id': user.id,
                'username': user_info.get('username', user.username),  # 使用外部API的用户名
                'company_name': user_info.get('company_name', user.company_name)  # 使用外部API的公司名称
            }
        }, "登录成功"
    
    @staticmethod
    def get_scores(token):
        """获取用户积分信息"""
        try:
            headers = {
                'accept': 'application/json, text/plain, */*',
                'authorization': f'Bearer {token}',
                'clientid': RefactoredConfig.CLIENT_ID,
                'content-language': 'zh_CN',
            }
            response = requests.get(
                f"{RefactoredConfig.BASE_URL}/progress/app/regularStudyRecord/getRegularFractionInfo",
                headers=headers
            )
            
            # 检查响应状态
            if response.status_code != 200:
                print(f"获取积分信息失败: HTTP状态码 {response.status_code}")
                return None
                
            data = response.json()
            if data and data.get('code') == 200:
                return {
                    'total_score': data['data']['totalScore'],
                    'monthly_score': data['data']['obtainScore']
                }
            else:
                error_msg = data.get('msg', '未知错误') if data else '响应数据为空'
                print(f"获取积分信息失败: {error_msg}")
                return None
        except Exception as e:
            print(f"调用积分信息API时发生异常: {e}")
            return None
    
    @staticmethod
    def get_task_status(token):
        """获取任务完成情况（三个一：每日一题、每周一课、每月一考）"""
        try:
            headers = {
                'accept': 'application/json, text/plain, */*',
                'authorization': f'Bearer {token}',
                'clientid': RefactoredConfig.CLIENT_ID,
                'content-language': 'zh_CN',
            }
            response = requests.get(
                f"{RefactoredConfig.BASE_URL}/progress/app/regularStudy/getNewRegularStudyList",
                headers=headers
            )
            
            # 检查响应状态
            if response.status_code != 200:
                print(f"获取任务完成情况失败: HTTP状态码 {response.status_code}")
                return None
                
            data = response.json()
            if data and data.get('code') == 200:
                response_data = data.get('data', {})
                
                # 解析三个任务的状态
                daily_info = response_data.get('regularStudyDayInfo', {})
                weekly_info = response_data.get('repeatCourseWeekInfo', {})
                monthly_info = response_data.get('regularExamMonthInfo', {})
                
                # 状态映射：1=未完成，2=已完成
                status_map = {
                    1: '未完成',
                    2: '已完成'
                }
                
                return {
                    'daily': {
                        'name': daily_info.get('studyName', '每日一题'),
                        'status': status_map.get(daily_info.get('studyStatus', 1), '未知'),
                        'available_score': daily_info.get('availableScore', 0),
                        'obtained_score': daily_info.get('obtainedScore', 0)
                    },
                    'weekly': {
                        'name': weekly_info.get('courseName', '每周一课'),
                        'status': status_map.get(weekly_info.get('studyStatus', 1), '未知'),
                        'available_score': weekly_info.get('availableScore', 0),
                        'obtained_score': weekly_info.get('obtainedScore', 0)
                    },
                    'monthly': {
                        'name': monthly_info.get('examName', '每月一考'),
                        'status': status_map.get(monthly_info.get('studyStatus', 1), '未知'),
                        'available_score': monthly_info.get('availableScore', 0),
                        'obtained_score': monthly_info.get('obtainedScore', 0)
                    }
                }
            else:
                error_msg = data.get('msg', '未知错误') if data else '响应数据为空'
                print(f"获取任务完成情况失败: {error_msg}")
                return None
        except Exception as e:
            print(f"调用任务完成情况API时发生异常: {e}")
            return None
