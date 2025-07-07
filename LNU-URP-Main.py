import os
import sys

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
    sys.stdout = open(os.devnull, "w")
    ocr = ddddocr.DdddOcr()
    ocr.set_ranges(6)
    sys.stdout = sys.__stdout__

    TodoList = UrpUtils.GetTodoList()

    # URL
    login_page_url = "http://jwstudent.lnu.edu.cn/"
    login_url = "http://jwstudent.lnu.edu.cn/j_spring_security_check"
    auth_url = "http://jwstudent.lnu.edu.cn/index"
    courseListURL = (
        "http://jwstudent.lnu.edu.cn/student/courseSelect/planCourse/courseList"
    )

    # 创建一个会话对象
    session = requests.Session()
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

    # 自动答题
    UrpUtils.AutoAnswerQuestion(session)

    # 执行批量选课
    UrpUtils.batch_select_courses(session, retry_times=2)
    os.system("pause")


if __name__ == "__main__":
    main()
