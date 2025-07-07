import json
import os


def main():
    print("鸟专抢课脚本 - 生成待选课程列表")
    print("=" * 50)
    if os.path.exists("TodoList.json"):
        # 如果文件已存在，询问是否覆盖
        overwrite = input("TodoList.json 已存在，是否覆盖？(y/n): ").strip().lower()
        if overwrite == "y":
            os.remove("TodoList.json")
        else:
            print("操作已取消，未覆盖 TodoList.json")
            return

    print("输入你要选几节课:")
    try:
        num_courses = int(input("请输入课程数量: "))
        if num_courses <= 0:
            raise ValueError("课程数量必须大于0")
    except ValueError as e:
        print(f"输入错误: {e}")
        return
    # 打开文件
    with open("TodoList.json", "w", encoding="utf-8") as file:
        TodoList = []
        for _ in range(num_courses):
            course = {
                "courseNum": input("请输入课程编号(e.g. 1420013): "),
                "classNum": input("请输入班级编号(e.g. 01): "),
                "kcm": "",
                "dealType": "2",
            }
            TodoList.append(course)
        json.dump(TodoList, file, ensure_ascii=False, indent=4)
    print("\nTodoList已保存到文件 'TodoList.json'。")


if __name__ == "__main__":
    main()
