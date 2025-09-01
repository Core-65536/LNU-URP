import os
import json
import random
import time

import requests

import UrpMD5
import UrpNet
import re

from bs4 import BeautifulSoup


# 获取课程名称的ASCII码并转成url格式
def Getkcms(course, courseNum):
    kcms = ""
    for i in course:
        kcms += str(ord(i)) + ","
    kcms += str(ord("_")) + ","
    for i in courseNum:
        kcms += str(ord(i)) + ","
    return kcms.replace(",", "%2C")


# 将密码进行MD5加密
def md5_encode(passwd):
    encoded = (
        UrpMD5.hex_md5(UrpMD5.hex_md5(passwd, ""), "1.8")
        + "*"
        + UrpMD5.hex_md5(UrpMD5.hex_md5(passwd, "1.8"), "1.8")
    )
    return encoded


# OCR获取验证码
def get_captcha(session, ocr):
    # 获取验证码
    captcha_url = "http://jwstudent.lnu.edu.cn/img/captcha.jpg"
    response = UrpNet.Loop_GET(session, captcha_url, {})
    captcha_file = "captcha" + str(random.randint(0, 100000)) + ".jpg"
    with open(captcha_file, "wb") as f:
        f.write(response.content)
    # OCR识别验证码
    image = open(captcha_file, "rb").read()
    result = ocr.classification(image)
    # 排除常见识别错误
    if len(result) == 5:
        result = result[1:5]
    captcha_code = result
    print("captcha_code = " + captcha_code)
    os.remove(captcha_file)

    return result


# 获取tokenValue
def GetTokenValue(session, login_page_url):
    # 发送GET请求以获取登录页面HTML
    rp = UrpNet.Loop_GET(session, login_page_url, {})
    html = rp.text
    # 使用BeautifulSoup解析HTML
    soup = BeautifulSoup(html, "html.parser")
    # 提取 tokenValue
    token_value = soup.find("input", {"id": "tokenValue"})["value"]
    print(f"Token Value: {token_value}")

    return token_value


def get_token_from_html(html_content):
    """
    从给定的HTML文本中安全地解析出id为'tokenValue'的input标签的值。

    Args:
        html_content: 页面的完整HTML字符串。

    Returns:
        如果找到，则返回token字符串；如果未找到，则返回 None。
    """
    if not html_content:
        print("错误：传入的HTML内容为空。")
        return None

    try:
        # 使用BeautifulSoup解析HTML
        soup = BeautifulSoup(html_content, "html.parser")

        # 查找id为'tokenValue'的input标签
        token_input = soup.find("input", {"id": "tokenValue"})

        # 核心改进：检查是否找到了标签，并且该标签有'value'属性
        if token_input and token_input.has_attr("value"):
            token_value = token_input["value"]
            return token_value
        else:
            # 如果没有找到，给出明确提示
            print("未在HTML中找到 id='tokenValue' 的input标签或其没有'value'属性。")
            return None

    except Exception as e:
        print(f"解析HTML时发生未知错误: {e}")
        return None


# 获取方案计划号
ChooseCourseURL = "http://jwstudent.lnu.edu.cn/student/courseSelect/gotoSelect/index"


def Getfajhh(session):
    rp = UrpNet.Loop_GET(session, ChooseCourseURL, {})
    pos = rp.text.find("fajhh=")
    pos2 = rp.text.find("'", pos + 1)
    fajhh = rp.text[pos + 6 : pos2]
    return fajhh


def GetTermCode(session):
    planCourseURL = (
        "http://jwstudent.lnu.edu.cn/student/courseSelect/planCourse/index?fajhh="
    )
    rp = UrpNet.Loop_GET(session, planCourseURL + Getfajhh(session), {})
    pattern = re.compile(r'<option value="([^"]+)"[^>]*\bselected\b[^>]*>')
    termCode = pattern.findall(rp.text)[0]
    return termCode


# 获取课程列表
def GetCourseList(session, courseListURL):
    # 获取方案计划号
    fajhh = Getfajhh(session)
    # 获取课程列表
    rp = UrpNet.Loop_POST(
        session,
        courseListURL,
        data={
            "fajhh": fajhh,
            "xq": 0,
            "jc": 0,
        },
    )
    # 课程列表
    courseList = rp.json()
    return courseList


# 获取需要抢的课
def GetTodoList():
    with open("TodoList.json", "r", encoding="utf-8") as file:
        TodoList = json.load(file)
    return TodoList


# 获取某一学期课程成绩
def GetCourseGrades(session, academic_year_code, term_code):
    # 首先获取callback前的随机生成的十位字符
    GradesUrl = "http://jwstudent.lnu.edu.cn/student/integratedQuery/scoreQuery/allPassingScores/index"
    UrpNet.Set_headers(
        "http://jwstudent.lnu.edu.cn/student/integratedQuery/scoreQuery/coursePropertyScores/index"
        "?mobile=false"
    )
    rp = UrpNet.Loop_GET(session, GradesUrl, data={})
    pos = rp.text.find("/callback") - 27
    token = rp.text[pos : pos + 10]
    # 拼接成绩查询url
    GradesUrl = (
        "http://jwstudent.lnu.edu.cn/student/integratedQuery/scoreQuery/"
        + token
        + "/allPassingScores/callback"
    )
    UrpNet.Set_headers(
        "http://jwstudent.lnu.edu.cn/student/integratedQuery/scoreQuery/allPassingScores/index?mobile"
        "=false"
    )
    rp = json.loads(UrpNet.Loop_GET(session, GradesUrl, data={}).text)
    grades = []
    # 遍历获取当前学期成绩
    # print(rp["lnList"])
    if academic_year_code == "all":
        for term in rp["lnList"]:
            grades.extend(term["cjList"])
    else:
        for term in rp["lnList"]:
            if (
                term["cjbh"] == f"{academic_year_code}学年秋(两学期)"
                and term_code == "1"
            ):
                grades.extend(term["cjList"])
            elif (
                term["cjbh"] == f"{academic_year_code}学年春(两学期)"
                and term_code == "2"
            ):
                grades.extend(term["cjList"])
    # 输出成绩
    TotalCredits = 0.00
    scores = 0.00
    gpa = 0.00

    if not grades:
        print("该学期暂无成绩记录")
        return 0

    for grade in grades:
        try:
            course_name = grade.get("courseName", "未知课程")
            course_score = grade.get("courseScore", "0")
            credit = float(grade.get("credit", 0))
            grade_point = float(grade.get("gradePointScore", 0))

            # 处理成绩可能为非数字的情况（如"优秀"、"及格"等）
            try:
                course_score_num = float(course_score)
            except ValueError:
                # 如果成绩不是数字，跳过该课程的分数计算，但仍计算学分
                print(
                    f"课程名称: {course_name}, 成绩: {course_score} (非数字成绩，跳过分数计算)"
                )
                TotalCredits += credit
                continue

            print(f"课程名称: {course_name}, 成绩: {course_score}")
            TotalCredits += credit
            scores += course_score_num * credit
            gpa += grade_point * credit

        except (ValueError, TypeError, KeyError) as e:
            print(f"处理成绩数据时出现错误: {e}, 跳过该条记录")
            continue

    # 检查是否有有效的成绩数据，避免除零错误
    if TotalCredits > 0:
        avg_score = scores / TotalCredits if scores > 0 else 0
        avg_gpa = gpa / TotalCredits if gpa > 0 else 0
        print(
            f"总学分: {TotalCredits}, 加权平均分: %.4f , 加权平均绩点: %.4f"
            % (avg_score, avg_gpa)
        )
    else:
        print("该学期暂无有效成绩数据或学分总计为0")

    return len(grades)


def GetCourseNameList(TodoList, dealType):
    courseList = ""
    for course in TodoList:
        if course["dealType"] == dealType:
            courseList += (
                Getkcms(course["kcm"], course["classNum"]) + "," + str(ord(",")) + ","
            )
    courseList = courseList[0 : len(courseList) - 4]
    # print(courseList)
    return courseList.replace(",", "%2C")


def GetCourseID(session, ToDoList):
    CourseID = ""
    for course in ToDoList:
        CourseID += course["courseNum"] + "_" + course["classNum"] + "_"
        CourseID += GetTermCode(session) + ","
    CourseID = CourseID[0 : len(CourseID) - 1]
    return CourseID


base_headers = {
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Cache-Control": "no-cache",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Pragma": "no-cache",
    "Proxy-Connection": "keep-alive",
    "X-Requested-With": "XMLHttpRequest",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
}

# 你的学校教务系统域名
base_url = "http://jwstudent.lnu.edu.cn"


# 2. 访问选课主页，获取初始 CSRF Token
# --------------------------------------
def get_initial_token(session):
    """
    访问选课主页面，抓取并返回最新的CSRF Token。
    """
    # 这个URL是从你提供的fetch请求的Referer中找到的
    select_course_home_url = f"{base_url}/student/courseSelect/gotoSelect/index?mobile="

    # 设置页面请求的Referer
    UrpNet.Set_headers(f"{base_url}/")

    try:
        response = UrpNet.Loop_GET(session, select_course_home_url, {})

        soup = BeautifulSoup(response.text, "html.parser")
        token_input = soup.find("input", {"id": "tokenValue"})

        if token_input and "value" in token_input.attrs:
            print(f"成功获取到初始Token: {token_input['value']}")
            return token_input["value"]
        else:
            print("错误：在页面中未找到 #tokenValue。")
            # 检查是否登录失效或页面结构已改变
            # print(response.text) # 打印页面内容帮助调试
            return None
    except Exception as e:
        print(f"错误：获取初始Token时发生异常: {e}")
        return None


def select_single_course(token, session, course_info):
    """
    选择单个课程
    :param token: CSRF Token
    :param session: 请求会话
    :param course_info: 课程信息字典，包含courseNum, classNum, kcm, dealType
    :return: 新的token值，如果失败返回None
    """
    base_url = "http://jwstudent.lnu.edu.cn"
    if not token:
        print("操作中止：无效的Token。")
        return None

    submit_url = f"{base_url}/student/courseSelect/selectCourse/checkInputCodeAndSubmit"

    # 构建单个课程的ID
    term_code = GetTermCode(session)
    course_id = f"{course_info['courseNum']}_{course_info['classNum']}_{term_code}"

    # 构建单个课程的kcms参数
    course_name_encoded = Getkcms(course_info["kcm"], course_info["classNum"])

    payload = {
        "dealType": course_info["dealType"],
        "fajhh": Getfajhh(session),
        "kcIds": course_id,
        "kcms": course_name_encoded,
        "sj": "0_0",
        "kclbdm": "",
        "kzh": "",
        "xqh": "",
        "inputCode": "undefined",
        "tokenValue": token,
    }

    print(
        f"正在选课: {course_info['kcm']} ({course_info['courseNum']}_{course_info['classNum']})"
    )

    # 设置选课请求的Referer
    UrpNet.Set_headers(f"{base_url}/student/courseSelect/gotoSelect/index?mobile=")

    try:
        response = UrpNet.Loop_POST(session, submit_url, payload)

        json_response = response.json()

        # print(json_response)

        if json_response["result"] == "ok":
            print(f"选课成功: {course_info['kcm']}")
            return json_response.get("token")
        else:
            print(f"选课失败: {course_info['kcm']} - {json_response}")
            return json_response.get("token")

    except Exception as e:
        print(f"网络请求异常: {course_info['kcm']} - {e}")
        return None


def select_course(token, session, TodoList):
    """
    根据TodoList依次选择所有课程
    :param token: 初始CSRF Token
    :param session: 请求会话
    :param TodoList: 待选课程列表
    :return: 选课结果统计
    """
    if not token:
        print("操作中止：无效的Token。")
        return {"success": 0, "failed": 0, "total": 0}

    if not TodoList:
        print("TodoList为空，没有课程需要选择。")
        return {"success": 0, "failed": 0, "total": 0}

    current_token = token
    success_count = 0
    failed_count = 0
    total_count = len(TodoList)

    print(f"开始批量选课，共{total_count}门课程")
    print("=" * 50)

    for i, course in enumerate(TodoList, 1):
        print(f"\n[{i}/{total_count}] 处理课程...")

        # 选择单个课程
        new_token = select_single_course(current_token, session, course)

        if new_token:
            # 更新token用于下一次请求
            current_token = new_token
            success_count += 1
        else:
            failed_count += 1
            # 如果token失效，尝试重新获取
            print("Token可能失效，尝试重新获取...")
            current_token = get_initial_token(session)
            if not current_token:
                print("无法获取新Token，终止选课流程。")
                break

        # 添加短暂延迟避免请求过快
        import time

        time.sleep(0.2)

    print("\n" + "=" * 50)
    print(f"选课结果统计:")
    print(f"   成功: {success_count}门")
    print(f"   失败: {failed_count}门")
    print(f"   总计: {total_count}门")
    print(f"   成功率: {(success_count/total_count*100):.1f}%")

    return {
        "success": success_count,
        "failed": failed_count,
        "total": total_count,
        "final_token": current_token,
    }


def batch_select_courses(session, retry_times=3):
    """
    批量选课的便捷函数
    :param session: 已登录的会话
    :param retry_times: 失败重试次数
    :return: 选课结果统计
    """
    # 获取待选课程列表
    todo_list = GetTodoList()

    if not todo_list:
        print("TodoList为空，请先配置待选课程。")
        return {"success": 0, "failed": 0, "total": 0}

    print(f"待选课程列表:")
    for i, course in enumerate(todo_list, 1):
        print(f"   {i}. {course['kcm']} ({course['courseNum']}_{course['classNum']})")

    # 获取初始token
    print("\n获取初始Token...")
    initial_token = get_initial_token(session)

    if not initial_token:
        print("无法获取初始Token，选课失败。")
        return {"success": 0, "failed": 0, "total": 0}

    # 开始选课
    result = select_course(initial_token, session, todo_list)

    # 如果有失败的课程且还有重试次数，尝试重试
    if result["failed"] > 0 and retry_times > 0:
        print(f"\n检测到失败课程，将进行重试（剩余重试次数: {retry_times}）")

        # 构建失败课程列表（这里简化处理，实际应该记录失败的具体课程）
        # 由于当前实现没有记录具体失败的课程，这里只是示例
        # 在实际使用中，可以修改select_course函数来返回失败的课程列表
        if result["failed"] == len(todo_list):
            # 如果全部失败，重试全部
            time.sleep(2)  # 等待2秒后重试
            retry_result = batch_select_courses(session, retry_times - 1)
            return retry_result

    return result


def AutoAnswerQuestion(session):
    """
    从HTML中解析第一个问题的ID，并循环发送POST请求尝试答案A, B, C, D。

    参数:
    - html_content (str): 包含问题数据的页面HTML文本。
    - session (requests.Session): 一个已经包含了登录信息的requests session对象。
                                  这是关键，必须是登录后的session。
    """

    # 1. 使用正则表达式从JS代码中提取问题数据字符串
    # 这个正则表达式会寻找 var question = eval('...'); 这部分
    page_url = "http://jwstudent.lnu.edu.cn/student/courseSelect/courseSelect/index"
    html_content = UrpNet.Loop_GET(session, page_url, {}).text
    match = re.search(r"var question = eval\('(.+?)'\);", html_content)
    if not match:
        print("错误：在HTML文件中没有找到问题数据，题目可能已经完成。")
        return

    try:
        # 2. 将提取的字符串解析为Python列表
        questions_data = json.loads(match.group(1))
    except json.JSONDecodeError:
        print("错误：解析问题数据时出错，格式可能不是标准的JSON。")
        return

    if not questions_data:
        print("错误：问题数据为空。")
        return

    # 3. 获取第一个问题的ID
    first_question_id = questions_data[0][0]
    print(f"成功获取到问题ID: {first_question_id}")

    # 4. 定义目标URL和要尝试的答案
    check_url = (
        "http://jwstudent.lnu.edu.cn/student/courseSelect/viewSelectCoursePaper/checkDa"
    )
    answers_to_try = ["A", "B", "C", "D"]

    # 5. 循环发送POST请求
    for answer in answers_to_try:
        # 构造POST请求的数据
        payload = {"info": f"{first_question_id}@{answer}"}

        try:
            # 发送请求，不关心返回结果
            UrpNet.Loop_POST(session, check_url, payload)
        except requests.exceptions.RequestException as e:
            print(f"发送答案 '{answer}' 时发生网络错误: {e}")

    print("自动答题已完成.")


def extract_question_ids(html_content):
    """
    从教学评估页面的HTML内容中解析出所有问题的ID。

    Args:
        html_content: 页面的完整HTML文本。

    Returns:
        一个包含所有问题ID字符串的列表。
    """
    # 使用BeautifulSoup进行解析
    soup = BeautifulSoup(html_content, "html.parser")

    # 找到所有data-name属性为'szt'的input标签，这是此类分数题的共同特征
    question_inputs = soup.find_all("input", {"data-name": "szt"})

    # 从找到的标签中提取name属性值（即ID）
    question_ids = [tag["name"] for tag in question_inputs if tag.has_attr("name")]

    return question_ids
