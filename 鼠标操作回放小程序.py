from pynput.mouse import Button, Controller
from pynput.keyboard import Listener, Key
import json
import time
from queue import Queue

command_queue = Queue(maxsize=1)
is_infinite_repeat = False
is_paused = False

def on_press(key):
    global is_infinite_repeat, is_paused
    try:
        if key.char == 'r':
            is_infinite_repeat = not is_infinite_repeat
            print(f"\n{'开启' if is_infinite_repeat else '关闭'}")
            command_queue.put("R_PRESSED")
        elif key.char == 's':
            is_paused = not is_paused
            print(f"\n{'暂停' if is_paused else '恢复'}回放")
            command_queue.put("TOGGLE_PAUSE")

    except AttributeError:
        if key == Key.esc:
            print("\n检测到Esc，即将停止回放")
            command_queue.put("STOP")
            return False

def read_mouse_data(file_path):
    """从JSON文件中读取鼠标操作数据"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            mouse_logs = json.load(f)
            if isinstance(mouse_logs, list) and mouse_logs:
                print(f'成功从"{file_path}"读取了{len(mouse_logs)}条操作')
                return mouse_logs
            else:
                print('JSON文件内容格式不正确，应为一个操作对象的列表')
                return None
    except FileNotFoundError:
        print(f'错误: 文件{file_path}未找到')
        return None
    except json.JSONDecodeError:
        print(f'错误:文件“{file_path}”不是有效的JSON格式.')
        return None

def _single_replay(actions):
    """
    执行单次回访的内部函数。
    如果在回放过程中收到STOP或REPEAT指令，会提前中断并返回指令
    """
    mouse = Controller()
    last_action_time = actions[0]['time']

    for action in actions:
        if not command_queue.empty():
            cmd = command_queue.get()
            if cmd == "STOP":
                return "STOP"
            elif cmd == "TOGGLE_PAUSE":
                global is_paused
                is_paused = not is_paused
                while is_paused:
                    if not command_queue.empty():
                        sub_cmd = command_queue.get()
                        if sub_cmd == "STOP":
                            return "STOP"
                        elif sub_cmd == "TOGGLE_PAUSE":
                            is_paused = not is_paused
                            print("\n 恢复回放")
                            break
                    time.sleep(0.1)

        delay = action['time'] - last_action_time
        if delay > 0:
            start_sleep_time = time.time()
            while time.time() - start_sleep_time < delay:
                time.sleep(0.01)
                if not command_queue.empty():
                    cmd = command_queue.get()
                    if cmd == "STOP":
                        return "STOP"
                    elif cmd == "TOGGLE_PAUSE":
                        is_paused = not is_paused
                        while is_paused:
                            if not command_queue.empty():
                                sub_cmd = command_queue.get()
                                if sub_cmd == "STOP":
                                    return "STOP"
                                elif sub_cmd == "TOGGLE_PAUSE":
                                    is_paused = not is_paused
                                    print("\n恢复回放")
                            time.sleep(0.1)

        action_type = action['type']
        x, y = action['x'], action['y']
        mouse.position = (x, y)
        print(f"时间:{action['time']:.2f},类型:{action_type},位置:({x},{y})")

        if action_type == 'click':
            button = Button.left if action['button'] == 'left' else Button.right
            if action['pressed']:
                mouse.press(button)
                print(f"按下鼠标{action['button']}键")
            else:
                mouse.release(button)
                print(f"释放鼠标{action['button']}按键")

        elif action_type == 'scroll':
            mouse.scroll(action['dx'], action['dy'])
            print(f"滚动：(dx={action['dx']}, dy={action['dy']})")

        last_action_time = action['time']

    return "FINISHED"

def replay_mouse_actions(actions):

    if not actions:
        print('没有可回放的鼠标操作')
        return

    print("键盘监听器已启动：\n 按 R 键，切换[无限重复]模式(开/关). \n按S键：暂停/恢复回放 \n按 Esc键，停止并退出程序")

    listener = Listener(on_press=on_press, daemon=True)
    listener.start()

    global is_infinite_repeat, is_paused
    print("\n请按R建确认开始无限重复回放，或按ESC键退出")
    while True:
        if not command_queue.empty():
            cmd = command_queue.get()
            if cmd =="R_PRESSED" or cmd =="REPEAT":
                is_infinite_repeat = True
                print("\n 用户确认,---开始新一轮回放---")
                break
            elif cmd == "STOP":
                print("用户取消，此程序退出。")
                listener.stop()
                return
        time.sleep(0.1)

    while is_infinite_repeat:
        print("\n---开始新一轮回放---")
        result = _single_replay(actions)

        if result == 'STOP':
            print("收到停止指令，程序将退出")
            break

        if not is_infinite_repeat:
            print("本轮回放正常完成(未开启无限重复)")
            break

        while is_paused:
            if not command_queue.empty():
                cmd = command_queue.get()
                if cmd == "STOP":
                    print("收到停止指令，程序即将退出")
                    listener.stop()
                    return
                elif cmd == "TOGGLE_PAUSE":
                    is_paused = not is_paused
                    printj("\n恢复回放")
            time.sleep(0.1)
        print("本轮回放完成，继续下一轮（已开启无限重复）")
    print("程序已停止")
    listener.stop()

if __name__ == '__main__':
    print("停止:Esc\nR:无限重复\nS:暂停/恢复回放")
    json_file = input('请输入读取的文件名(文件名包括后缀)\n(并且确保这个文件和此python脚本在同一目录下):')
    mouse_actions = read_mouse_data(json_file)
    if mouse_actions:
        replay_mouse_actions(mouse_actions)

    input("脚本执行完毕，按回车键退出")