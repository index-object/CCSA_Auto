import requests
from datetime import datetime

from ccsa_auto.core.config import Config
from ccsa_auto.modules.auth.service import AuthService

class TaskService:
    """任务服务"""
    
    @staticmethod
    def execute_daily_question(access_token, user_id):
        """
        执行每日一题
        """
        try:
            # 获取每日一题信息
            daily_url = Config.EXTERNAL_PLATFORM['API_ENDPOINTS']['DAILY_URL']
            response = requests.get(
                daily_url,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    **Config.EXTERNAL_PLATFORM['HEADERS']
                }
            )
            
            response_json = response.json()
            if response_json.get('code') == 200:
                # 这里需要根据实际API返回结构调整
                # 假设返回的是题目信息
                question_data = response_json.get('data', {})
                
                # 提交答案
                # 这里需要根据实际API调整
                # 假设答案是固定的或者可以从题目信息中获取
                answer_data = {
                    "questionId": question_data.get('id'),
                    "answer": "A"  # 假设答案是A
                }
                
                submit_response = requests.post(
                    daily_url,
                    json=answer_data,
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        **Config.EXTERNAL_PLATFORM['HEADERS']
                    }
                )
                
                submit_json = submit_response.json()
                if submit_json.get('code') == 200:
                    return {
                        'success': True,
                        'message': '每日一题执行成功',
                        'result': submit_json.get('data', {})
                    }
                else:
                    return {
                        'success': False,
                        'message': f"提交答案失败: {submit_json.get('msg', '未知错误')}"
                    }
            else:
                return {
                    'success': False,
                    'message': f"获取每日一题失败: {response_json.get('msg', '未知错误')}"
                }
        except Exception as e:
            return {
                'success': False,
                'message': f"执行每日一题异常: {str(e)}"
            }
    
    @staticmethod
    def execute_weekly_lesson(access_token, user_id):
        """
        执行每周一课
        """
        try:
            weekly_url = Config.EXTERNAL_PLATFORM['API_ENDPOINTS']['WEEKLY_URL']
            response = requests.get(
                weekly_url,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    **Config.EXTERNAL_PLATFORM['HEADERS']
                }
            )
            
            response_json = response.json()
            if response_json.get('code') == 200:
                # 这里需要根据实际API返回结构调整
                # 假设返回的是课程信息
                lesson_data = response_json.get('data', {})
                
                # 提交学习记录
                # 这里需要根据实际API调整
                submit_data = {
                    "lessonId": lesson_data.get('id'),
                    "completed": True
                }
                
                submit_response = requests.post(
                    weekly_url,
                    json=submit_data,
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        **Config.EXTERNAL_PLATFORM['HEADERS']
                    }
                )
                
                submit_json = submit_response.json()
                if submit_json.get('code') == 200:
                    return {
                        'success': True,
                        'message': '每周一课执行成功',
                        'result': submit_json.get('data', {})
                    }
                else:
                    return {
                        'success': False,
                        'message': f"提交学习记录失败: {submit_json.get('msg', '未知错误')}"
                    }
            else:
                return {
                    'success': False,
                    'message': f"获取每周一课失败: {response_json.get('msg', '未知错误')}"
                }
        except Exception as e:
            return {
                'success': False,
                'message': f"执行每周一课异常: {str(e)}"
            }
    
    @staticmethod
    def execute_monthly_exam(access_token, user_id):
        """
        执行每月一考
        """
        try:
            monthly_url = Config.EXTERNAL_PLATFORM['API_ENDPOINTS']['MONTHLY_URL']
            response = requests.get(
                monthly_url,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    **Config.EXTERNAL_PLATFORM['HEADERS']
                }
            )
            
            response_json = response.json()
            if response_json.get('code') == 200:
                # 这里需要根据实际API返回结构调整
                # 假设返回的是考试信息
                exam_data = response_json.get('data', {})
                
                # 提交考试答案
                # 这里需要根据实际API调整
                submit_data = {
                    "examId": exam_data.get('id'),
                    "answers": {
                        "1": "A",
                        "2": "B",
                        "3": "C",
                        "4": "D",
                        "5": "A"
                    }
                }
                
                submit_response = requests.post(
                    monthly_url,
                    json=submit_data,
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        **Config.EXTERNAL_PLATFORM['HEADERS']
                    }
                )
                
                submit_json = submit_response.json()
                if submit_json.get('code') == 200:
                    return {
                        'success': True,
                        'message': '每月一考执行成功',
                        'result': submit_json.get('data', {})
                    }
                else:
                    return {
                        'success': False,
                        'message': f"提交考试答案失败: {submit_json.get('msg', '未知错误')}"
                    }
            else:
                return {
                    'success': False,
                    'message': f"获取每月一考失败: {response_json.get('msg', '未知错误')}"
                }
        except Exception as e:
            return {
                'success': False,
                'message': f"执行每月一考异常: {str(e)}"
            }
    
    @staticmethod
    def execute_task(task, user):
        """
        执行任务
        """
        try:
            # 1. 验证外部平台账号
            if not user.external_username or not user.external_password:
                return {
                    'success': False,
                    'message': '未设置外部平台账号信息'
                }
            
            # 外部平台认证
            auth_success, user_info, access_token = AuthService.authenticate_external(
                user.external_username, 
                '123456'  # 这里需要根据实际情况获取密码
            )
            if not auth_success:
                return {
                    'success': False,
                    'message': '外部平台认证失败'
                }
            
            # 2. 执行任务
            if task.task_type == 'daily':
                result = TaskService.execute_daily_question(access_token, user.id)
            elif task.task_type == 'weekly':
                result = TaskService.execute_weekly_lesson(access_token, user.id)
            elif task.task_type == 'monthly':
                result = TaskService.execute_monthly_exam(access_token, user.id)
            else:
                return {
                    'success': False,
                    'message': '任务类型无效'
                }
            
            return result
        except Exception as e:
            return {
                'success': False,
                'message': f"执行任务异常: {str(e)}"
            }
