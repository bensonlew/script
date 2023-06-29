import os
import readline
from transformers import pipeline

# 创建transformers自然语言处理pipeline
fill_mask = pipeline("fill-mask")

# 自定义readline自动补全函数
def completer(text, state):
    # 获取当前输入的命令行
    cmd = readline.get_line_buffer()

    # 检查是否存在未完成的命令或参数
    if not cmd or cmd[-1] in [' ', '\t']:
        prefix = text
    else:
        prefix = cmd.split()[-1] + text

    # 使用transformers的fill-mask函数生成自动补全建议
    suggestions = fill_mask(f"{prefix} [MASK]")[0]["sequence"].split()[-1]

    # 根据当前输入返回匹配的自动补全建议
    matches = [s for s in suggestions if s.startswith(text)]

    # 如果存在多个匹配建议，返回第一个建议
    if state < len(matches):
        return matches[state]
    else:
        return None

# 配置readline自动补全
readline.parse_and_bind("tab: complete")
readline.set_completer(completer)

# 进入命令行循环
while True:
    try:
        cmd = input("$ ")
        # 执行命令
        os.system(cmd)
    except KeyboardInterrupt:
        # 捕获ctrl+c中断命令行循环
        break
