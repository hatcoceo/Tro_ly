import time


def can_handle(command: str) ->bool:
    return command.lower().startswith('gọi kịch bản:')


def handle(command: str):
    print('🧠 Plugin ScriptCaller: Đang chạy kịch bản...')
    try:
        _, script_text = command.split(':', 1)
        lines = [line.strip() for line in script_text.strip().split(';') if
            line.strip()]
    except ValueError:
        print('❌ Cú pháp sai. Dùng: gọi kịch bản: dòng1; dòng2; ...')
        return
    labels = {}
    variables = {}
    pointer = 0
    for idx, line in enumerate(lines):
        if line.startswith('label '):
            label_name = line[6:].strip()
            labels[label_name] = idx
    while pointer < len(lines):
        line = lines[pointer]
        if line.startswith('#'):
            pointer += 1
            continue
        elif line.startswith('label '):
            pointer += 1
            continue
        elif line.startswith('set '):
            try:
                _, expr = line.split('set', 1)
                var, val = expr.split('=', 1)
                variables[var.strip()] = val.strip()
            except:
                print(f'❌ Cú pháp set sai: {line}')
            pointer += 1
        elif line.startswith('input '):
            var = line[6:].strip()
            val = input(f'Nhập giá trị cho {var}: ')
            variables[var] = val
            pointer += 1
        elif line.startswith('wait '):
            try:
                secs = float(line[5:].strip())
                print(f'⏳ Đang chờ {secs} giây...')
                time.sleep(secs)
            except:
                print('❌ Lỗi cú pháp wait')
            pointer += 1
        elif line.startswith('goto '):
            label = line[5:].strip()
            if label in labels:
                pointer = labels[label]
            else:
                print(f"❌ Không tìm thấy nhãn '{label}'")
                break
        elif line.startswith('if '):
            try:
                parts = line[3:].split('goto')
                condition = parts[0].strip()
                label = parts[1].strip()
                var, op, value = condition.split()
                real_value = variables.get(var, '')
                if op == '==' and real_value == value:
                    if label in labels:
                        pointer = labels[label]
                        continue
            except:
                print(f'❌ Lỗi cú pháp if: {line}')
            pointer += 1
        elif line == 'break':
            print('🛑 Dừng kịch bản')
            break
        else:
            for k, v in variables.items():
                line = line.replace(f'{{{k}}}', v)
            print(f'➡ Gọi plugin: {line}')
            assistant.process_command(line)
            pointer += 1


def register(a):
    global assistant
    assistant = a
    a.handlers.insert(0, type('MultiPluginScriptHandler', (), {'can_handle':
        staticmethod(can_handle), 'handle': staticmethod(handle)})())


plugin_info = {'enabled': False, 'register': register, 'command_handle': [
    'gọi kịch bản:']}
