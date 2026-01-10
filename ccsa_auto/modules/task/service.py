import requests
import logging
from datetime import datetime, timedelta

from ccsa_auto.core.config import Config
from ccsa_auto.modules.auth.service import AuthService
from ccsa_auto.core.database import SessionLocal
from ccsa_auto.core.models import Task

# 配置日志记录
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# 创建日志记录器
logger = logging.getLogger(__name__)

class TaskService:
    """任务服务"""
    
    @staticmethod
    def execute_daily_question(access_token, user_id):
        """
        执行每日一题
        """
        try:
            import random
            import json
            
            logger.info(f"开始执行每日一题，用户ID: {user_id}")
            
            # 1. 获取每日一学列表
            study_url = Config.EXTERNAL_PLATFORM['API_ENDPOINTS']['GET_STUDY_LIST']
            study_headers = {
                "Authorization": f"Bearer {access_token}",
                **Config.EXTERNAL_PLATFORM['HEADERS']
            }
            
            logger.info(f"获取每日一学列表: {study_url}")
            study_response = requests.get(study_url, headers=study_headers)
            study_response_json = study_response.json()
            
            if study_response_json.get('code') != 200:
                error_msg = f"获取每日一学列表失败: {study_response_json.get('msg', '未知错误')}"
                logger.error(error_msg)
                return {
                    'success': False,
                    'message': error_msg
                }
            
            # 提取每日一学 ID
            study_data = study_response_json.get('data', {})
            daily_info = study_data.get('regularStudyDayInfo', {})
            study_id = daily_info.get('id')
            
            if not study_id:
                error_msg = '未能获取每日一学ID'
                logger.error(error_msg)
                return {
                    'success': False,
                    'message': error_msg
                }
            
            logger.info(f"获取到每日一学ID: {study_id}")
            
            # 2. 获取试题信息
            question_url = Config.EXTERNAL_PLATFORM['API_ENDPOINTS']['GET_DAILY_QUESTIONS']
            question_params = {
                'examAssociationId': study_id,
                'isReExam': 0,
                'regularStudyType': 1,
                'isRepair': 0
            }
            
            logger.info(f"获取试题信息: {question_url}")
            question_response = requests.get(
                question_url,
                params=question_params,
                headers=study_headers
            )
            question_response_json = question_response.json()
            
            if question_response_json.get('code') != 200:
                error_msg = f"获取试题信息失败: {question_response_json.get('msg', '未知错误')}"
                logger.error(error_msg)
                return {
                    'success': False,
                    'message': error_msg
                }
            
            # 封装试题数据
            question_data = question_response_json.get('data', {})
            question_list = question_data.get('questionList', [])
            
            questions = [
                {
                    "id": question.get("id"),
                    "questionType": question.get("questionType"),
                    "questionPoint": question.get("questionPoint"),
                    "questionAnswer": question.get("questionAnswera", "").strip('"')  # 去掉答案的引号
                }
                for question in question_list
            ]
            
            logger.info(f"获取到 {len(questions)} 道试题")
            
            # 3. 准备提交数据
            use_time = random.randint(120, 300)  # 随机生成 2~5 分钟的答题时间
            payload = {
                "practiceRegularId": study_id,
                "regularType": 2,
                "useTime": use_time,
                "isAgain": 0,
                "examType": 1,
                "isRepair": None,
                "courseExamAnswerInfoBos": questions,
                "fullPoint": 20,
                "examDuration": 30
            }
            
            # 4. 提交答案
            submit_url = Config.EXTERNAL_PLATFORM['API_ENDPOINTS']['SUBMIT_EXAM']
            submit_headers = {
                "Authorization": f"Bearer {access_token}",
                **Config.EXTERNAL_PLATFORM['HEADERS'],
                "Content-Type": "application/json;charset=UTF-8"
            }
            
            logger.info(f"提交每日一题答案: {submit_url}")
            submit_response = requests.post(
                submit_url,
                headers=submit_headers,
                data=json.dumps(payload)
            )
            submit_json = submit_response.json()
            
            if submit_json.get('code') == 200:
                logger.info("每日一题执行成功")
                return {
                    'success': True,
                    'message': '每日一题执行成功',
                    'result': submit_json.get('data', {})
                }
            else:
                error_msg = f"提交答案失败: {submit_json.get('msg', '未知错误')}"
                logger.error(error_msg)
                return {
                    'success': False,
                    'message': error_msg
                }
                
        except Exception as e:
            error_msg = f"执行每日一题异常: {str(e)}"
            logger.exception(error_msg)
            return {
                'success': False,
                'message': error_msg
            }
    
    @staticmethod
    def execute_weekly_lesson(access_token, user_id):
        """
        执行每周一课
        """
        try:
            import random
            import json
            
            # 1. 获取每周一课列表
            study_url = Config.EXTERNAL_PLATFORM['API_ENDPOINTS']['GET_STUDY_LIST']
            study_headers = {
                "Authorization": f"Bearer {access_token}",
                **Config.EXTERNAL_PLATFORM['HEADERS']
            }
            
            study_response = requests.get(study_url, headers=study_headers)
            study_response_json = study_response.json()
            
            if study_response_json.get('code') != 200:
                return {
                    'success': False,
                    'message': f"获取每周一课列表失败: {study_response_json.get('msg', '未知错误')}"
                }
            
            # 提取每周一课信息
            study_data = study_response_json.get('data', {})
            week_info = study_data.get('repeatCourseWeekInfo', {})
            week_id = week_info.get('id')
            week_resourceId = week_info.get('resourceId')
            
            if not week_id:
                return {
                    'success': False,
                    'message': '未能获取每周一课ID'
                }
            
            # 2. 获取课程详情
            weekly_url = Config.EXTERNAL_PLATFORM['API_ENDPOINTS']['GET_WEEKLY_LESSON'].replace('{lesson_id}', str(week_id))
            weekly_response = requests.get(
                f"{weekly_url}?id={week_id}",
                headers=study_headers
            )
            weekly_response_json = weekly_response.json()
            
            if weekly_response_json.get('code') != 200:
                return {
                    'success': False,
                    'message': f"获取课程详情失败: {weekly_response_json.get('msg', '未知错误')}"
                }
            
            # 提取课程信息
            lesson_info = weekly_response_json.get('data', {})
            resource_duration = lesson_info.get('resourceDuration', 300)
            resource_id = lesson_info.get('resourceId')
            lesson_id = lesson_info.get('id')
            
            # 3. 提交学习进度
            submit_url = Config.EXTERNAL_PLATFORM['API_ENDPOINTS']['SUBMIT_STUDY_SCHEDULE']
            submit_headers = {
                "Authorization": f"Bearer {access_token}",
                **Config.EXTERNAL_PLATFORM['HEADERS'],
                "Content-Type": "application/json;charset=UTF-8"
            }
            
            payload = {
                "studyProgressTime": resource_duration,
                "studyDuration": resource_duration,
                "studyAssociationId": lesson_id,
                "studyType": 4,
                "courseResourceRelationId": resource_id,
                "studySchedule": 100
            }
            
            submit_response = requests.post(
                submit_url,
                headers=submit_headers,
                json=payload
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
            import random
            import json
            
            # 1. 获取每月一考列表
            study_url = Config.EXTERNAL_PLATFORM['API_ENDPOINTS']['GET_STUDY_LIST']
            study_headers = {
                "Authorization": f"Bearer {access_token}",
                **Config.EXTERNAL_PLATFORM['HEADERS']
            }
            
            study_response = requests.get(study_url, headers=study_headers)
            study_response_json = study_response.json()
            
            if study_response_json.get('code') != 200:
                return {
                    'success': False,
                    'message': f"获取每月一考列表失败: {study_response_json.get('msg', '未知错误')}"
                }
            
            # 提取每月一考信息
            study_data = study_response_json.get('data', {})
            month_info = study_data.get('regularExamMonthInfo', {})
            month_id = month_info.get('id')
            
            if not month_id:
                return {
                    'success': False,
                    'message': '未能获取每月一考ID'
                }
            
            # 2. 获取试题信息
            question_url = Config.EXTERNAL_PLATFORM['API_ENDPOINTS']['GET_MONTHLY_QUESTIONS']
            question_params = {
                'examAssociationId': month_id,
                'isReExam': 0,
                'regularStudyType': 2,
                'isRepair': 0
            }
            
            question_response = requests.get(
                question_url,
                params=question_params,
                headers=study_headers
            )
            question_response_json = question_response.json()
            
            if question_response_json.get('code') != 200:
                return {
                    'success': False,
                    'message': f"获取试题信息失败: {question_response_json.get('msg', '未知错误')}"
                }
            
            # 封装试题数据
            question_data = question_response_json.get('data', {})
            question_list = question_data.get('questionList', [])
            
            questions = [
                {
                    "id": question.get("id"),
                    "questionType": question.get("questionType"),
                    "questionPoint": question.get("questionPoint"),
                    "questionAnswer": question.get("questionAnswera", "").strip('"')  # 去掉答案的引号
                }
                for question in question_list
            ]
            
            # 3. 准备提交数据
            use_time = random.randint(300, 500)  # 随机生成答题时间
            payload = {
                "practiceRegularId": month_id,
                "regularType": 2,
                "useTime": use_time,
                "isAgain": 0,
                "examType": 2,
                "isRepair": None,
                "courseExamAnswerInfoBos": questions,
                "fullPoint": 100,
                "examDuration": 80
            }
            
            # 4. 提交答案
            submit_url = Config.EXTERNAL_PLATFORM['API_ENDPOINTS']['SUBMIT_EXAM']
            submit_headers = {
                "Authorization": f"Bearer {access_token}",
                **Config.EXTERNAL_PLATFORM['HEADERS'],
                "Content-Type": "application/json;charset=UTF-8"
            }
            
            submit_response = requests.post(
                submit_url,
                headers=submit_headers,
                data=json.dumps(payload)
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
            
            # 外部平台认证 - 使用用户存储的密码
            # 注意：这里假设 external_password 是明文存储，实际应该解密
            auth_success, user_info, access_token = AuthService.authenticate_external(
                user.external_username,
                user.external_password  # 使用用户存储的密码
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
    
    @staticmethod
    def create_default_tasks_for_user(user_id):
        """
        为用户创建默认任务（每日一题、每周一课、每月一考）
        
        Args:
            user_id: 用户ID
            
        Returns:
            list: 创建的任务列表
        """
        db = SessionLocal()
        try:
            logger.info(f"为用户 {user_id} 创建默认任务")
            
            # 默认任务配置
            default_tasks = [
                {
                    'task_type': 'daily',
                    'task_name': '每日一题',
                    'description': '每天自动完成每日一题',
                    'cron_expression': '0 9 * * *',  # 每天9:00
                },
                {
                    'task_type': 'weekly',
                    'task_name': '每周一课',
                    'description': '每周自动完成每周一课',
                    'cron_expression': '0 10 * * 0',  # 每周日10:00
                },
                {
                    'task_type': 'monthly',
                    'task_name': '每月一考',
                    'description': '每月自动完成每月一考',
                    'cron_expression': '0 14 1 * *',  # 每月1号14:00
                }
            ]
            
            created_tasks = []
            
            for task_config in default_tasks:
                # 检查是否已存在相同类型的任务
                existing_task = db.query(Task).filter_by(
                    user_id=user_id,
                    task_type=task_config['task_type']
                ).first()
                
                if existing_task:
                    logger.info(f"用户 {user_id} 的 {task_config['task_name']} 任务已存在，跳过创建")
                    continue
                
                # 计算下次运行时间（明天9:00、下周日10:00、下月1号14:00）
                now = datetime.utcnow()
                next_run_time = None
                
                if task_config['task_type'] == 'daily':
                    # 明天9:00
                    next_run_time = datetime(now.year, now.month, now.day, 9, 0, 0) + timedelta(days=1)
                elif task_config['task_type'] == 'weekly':
                    # 下周日10:00
                    days_until_sunday = (6 - now.weekday()) % 7 or 7  # 0=周一, 6=周日
                    next_run_time = datetime(now.year, now.month, now.day, 10, 0, 0) + timedelta(days=days_until_sunday)
                elif task_config['task_type'] == 'monthly':
                    # 下月1号14:00
                    if now.month == 12:
                        next_run_time = datetime(now.year + 1, 1, 1, 14, 0, 0)
                    else:
                        next_run_time = datetime(now.year, now.month + 1, 1, 14, 0, 0)
                
                # 创建新任务
                new_task = Task(
                    user_id=user_id,
                    task_type=task_config['task_type'],
                    task_name=task_config['task_name'],
                    description=task_config['description'],
                    cron_expression=task_config['cron_expression'],
                    is_active=True,
                    task_data='{}',  # 空JSON
                    execution_status='pending',
                    external_status='unknown',
                    scheduled_time=datetime.utcnow(),
                    next_run_time=next_run_time
                )
                
                db.add(new_task)
                created_tasks.append(new_task)
                logger.info(f"为用户 {user_id} 创建 {task_config['task_name']} 任务成功")
            
            db.commit()
            
            # 刷新任务对象以获取ID
            for task in created_tasks:
                db.refresh(task)
            
            # 将新创建的任务添加到调度器
            from ccsa_auto.modules.task.scheduler import add_task_to_scheduler
            for task in created_tasks:
                try:
                    add_task_to_scheduler(task.id)
                    logger.info(f"任务 {task.id} 已添加到调度器")
                except Exception as e:
                    logger.error(f"将任务 {task.id} 添加到调度器失败: {e}")
            
            logger.info(f"为用户 {user_id} 创建了 {len(created_tasks)} 个默认任务并已添加到调度器")
            return created_tasks
            
        except Exception as e:
            db.rollback()
            logger.error(f"为用户 {user_id} 创建默认任务失败: {str(e)}")
            raise
        finally:
            db.close()
