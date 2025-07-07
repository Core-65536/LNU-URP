import os
import sys
import time
import json

import ddddocr
import requests

import UrpNet
import UrpUtils

# 从 AccountInfo.py 中导入账号和密码
from AccountInfo import account, password


def main():
    # 免责声明
    print("=" * 80)
    print("                              免责声明")
    print("=" * 80)
    print()
    print("本脚本仅供技术学习和研究使用，严禁用于任何违法违规行为。")
    print()
    print("使用本脚本即表示您同意以下条款：")
    print("1. 本脚本仅用于个人学习和技术研究，不得用于任何商业用途")
    print("2. 使用者需遵守所在学校的相关规定和法律法规")
    print("3. 因使用本脚本造成的任何后果由使用者自行承担")
    print("4. 开发者不承担任何因使用本脚本而产生的法律责任")
    print("5. 请合理使用，避免对服务器造成过大压力")
    print()
    print("如果您不同意以上条款，请立即停止使用本脚本。")
    print("=" * 80)
    print()

    # 等待用户确认
    while True:
        user_input = input("请输入 'I AGREE' 表示同意以上条款并继续使用: ")
        if user_input.strip().upper() == "I AGREE":
            print("感谢您的确认，程序将继续运行...")
            print()
            break
        elif user_input.strip().upper() in ["N", "NO", "EXIT", "QUIT"]:
            print("您选择不同意条款，程序即将退出。")
            sys.exit(0)
        else:
            print("请输入 'I AGREE' 来同意条款，或输入 'N' 退出程序。")

    # 初始化OCR
    print("正在初始化OCR...")
    sys.stdout = open(os.devnull, "w")
    ocr = ddddocr.DdddOcr()
    ocr.set_ranges(6)
    sys.stdout = sys.__stdout__
    print("OCR初始化完成")

    # URL
    login_page_url = "http://jwstudent.lnu.edu.cn/"
    login_url = "http://jwstudent.lnu.edu.cn/j_spring_security_check"
    auth_url = "http://jwstudent.lnu.edu.cn/index"

    # 创建一个会话对象
    session = requests.Session()

    print("正在登录...")
    # 获取验证码
    captcha_code = UrpUtils.get_captcha(session, ocr)
    # 获取 tokenValue
    token_value = UrpUtils.GetTokenValue(session, login_page_url)
    # 加密密码
    encrypted_password = UrpUtils.md5_encode(password)

    # 提交表单数据
    payload = {
        "j_username": account,
        "j_password": encrypted_password,
        "j_captcha": captcha_code,
        "tokenValue": token_value,  # 使用从页面提取的 tokenValue
    }

    # 发送POST请求，提交登录表单
    rp = UrpNet.Loop_POST(session, login_url, payload)
    # 访问需要认证的页面
    rp = UrpNet.Loop_GET(session, auth_url, {})
    # 输出页面内容
    if rp.text.find("欢迎您") != -1:
        print("登录成功 !")
    else:
        print("登录失败 !")
        quit()

    url = "http://jwstudent.lnu.edu.cn/student/teachingAssessment/evaluation/queryAll"
    req = UrpNet.Loop_POST(session, url, {"pageNum": 1, "pageSize": 30, "flag": "ktjs"})
    AssessList = req.json().get("data", {}).get("records", [])
    if not AssessList:
        print("没有可评教的课程。")
        return
    print(f"共找到 {len(AssessList)} 门课程需要评教。")
    print(
        "即将自动评教，默认每道题目均提交为满分20分，此操作不可撤销，是否继续 [Y/N] ?"
    )
    if input().strip().upper() != "Y":
        print("操作已取消。")
        return
    print("正在自动评教，请稍等...")
    for lesson in AssessList:
        KTID = lesson.get("KTID")
        WJBM = lesson.get("WJBM")
        # 获取问卷网页，分析问卷中五道题的ID
        url = (
            "http://jwstudent.lnu.edu.cn/student/teachingEvaluation/newEvaluation/evaluation/"
            + KTID
        )
        QuesReq = UrpNet.Loop_GET(session, url, {})
        if QuesReq.status_code != 200:
            print(f"获取问卷失败，状态码: {QuesReq.status_code}")
            continue
        # 提取问卷中的题目ID
        questions = UrpUtils.extract_question_ids(QuesReq.text)
        # Get TokenValue for the assessment
        token_value = UrpUtils.get_token_from_html(QuesReq.text)

        multipart_data = {
            "tjcs": (None, "2"),
            "wjbm": (None, WJBM),
            "ktid": (None, KTID),
            "tokenValue": (None, token_value),
            questions[0]: (None, "20"),
            questions[1]: (None, "20"),
            questions[2]: (None, "20"),
            questions[3]: (None, "20"),
            questions[4]: (None, "20"),
            "compare": (None, ""),  # 值为空的字段也需要包含
        }
        # print(multipart_data)
        UrpNet.Set_headers(
            "http://jwstudent.lnu.edu.cn/student/teachingEvaluation/newEvaluation/evaluation"
            + KTID
        )
        # 等待5s
        print(f"正在提交评教问卷, 课程名：{lesson.get('KCM')}...")
        print("请稍等5秒，提交评教问卷中...")
        time.sleep(5)

        req = UrpNet.Special_LOOP_POST(
            session,
            "http://jwstudent.lnu.edu.cn/student/teachingAssessment/baseInformation/questionsAdd/doSave",
            {"tokenValue": token_value},
            multipart_data,
        )
        print(f"课程名：{lesson.get('KCM')}提交成功！")
    print("所有课程自动评教已完成。")


if __name__ == "__main__":
    main()
