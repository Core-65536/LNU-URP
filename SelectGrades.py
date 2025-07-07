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

    # 显示查询选项菜单
    print("\n" + "=" * 50)
    print("            学期成绩查询系统")
    print("=" * 50)
    print("请选择查询选项：")
    print("1. 查询所有学期成绩")
    print("2. 查询指定学期成绩")
    print("3. 退出")
    print("=" * 50)

    while True:
        choice = input("请输入选项号码（1-3）: ").strip()

        if choice == "1":
            print("\n正在查询所有学期成绩...")
            UrpUtils.GetCourseGrades(session, "all", "")
            break

        elif choice == "2":
            print("\n请输入学期信息：")
            print("学年格式示例: 2024-2025")
            print("学期代码: 1=秋季学期, 2=春季学期")

            academic_year = input("请输入学年: ").strip()
            term_code = input("请输入学期代码: ").strip()

            if not academic_year or not term_code:
                print("输入不能为空，请重新选择。")
                continue

            print(f"\n正在查询 {academic_year} 学年第 {term_code} 学期成绩...")
            UrpUtils.GetCourseGrades(session, academic_year, term_code)
            break

        elif choice == "3":
            print("感谢使用，程序即将退出。")
            sys.exit(0)

        else:
            print("无效选项，请输入 1-3 之间的数字。")

    print("\n查询完成！")
    os.system("pause")


if __name__ == "__main__":
    main()
