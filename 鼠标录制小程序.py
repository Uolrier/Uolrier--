from pynput import mouse, keyboard
from pynput.mouse import Button, Listener, Controller
import json
import time

print('操作说明:\n按"Esc"停止\n按住"S"暂停，松开"S"继续录制',flush=True)

is_listening = True
is_paused = False

mouse_logs = []

def get_default_filename():
    input_file_name = input('请输入保存的文件名（直接回车使用默认名）：').strip()
    if not input_file_name:
        default_filename = 'mouse_record.json'
        print(f'未输入文件名，使用默认名称：{default_filename}')
        return default_filename
    else:
        return f'{input_file_name}.json'

final_filename = get_default_filename()

def on_press(key):
    global is_listening, is_paused
    if key == keyboard.Key.esc:
        is_listening = False
        print("正在停止...")
        listener.stop()
        return False
    elif key == keyboard.KeyCode.from_char('s'):
        if not is_paused:
            is_paused = True
            print('已暂停，松开"S"键继续监听')
def on_release(key):
    global is_paused
    if key == keyboard.KeyCode.from_char('s'):
        is_paused = False
        print('已继续监听...')

def on_move(x, y):
    if is_paused:
        return
    print(f'{x}, {y}')
    mouse_logs.append(
        {   'type' : 'move',
            'time': time.time(),
            'x': x,
            'y': y
        }
    )

def on_click(x, y, button, pressed):
    if is_paused:
        return
    button_text = 'left' if button == button.left else 'right'
    print(f'{x}, {y}, {button}, {pressed}')
    mouse_logs.append(
        { 'type' : 'click',
            'time': time.time(),
            'x': x,
            'y': y,
          'button': button_text,
          'pressed': pressed
        }
    )

def on_scroll(x, y, dx, dy):
    if is_paused:
        return
    print(f'{x}, {y}, {dx}, {dy}')
    mouse_logs.append(
        { 'type' : 'scroll',
          'time': time.time(),
          'x': x,
          'y': y,
          'dx': dx,
          'dy': dy}
    )

with (mouse.Listener(
        on_move=on_move,
        on_click=on_click,
        on_scroll=on_scroll
    )
    as listener):
        with keyboard.Listener(
            on_press=on_press,
            on_release=on_release
        ) as keyboard_listener:
            keyboard_listener.join()

with open(final_filename, 'w',encoding='utf-8') as f:
    json.dump(mouse_logs, f, ensure_ascii=False, indent=4)

print(f'日志已保存到: {final_filename}')

input("脚本执行结束按回车键退出")