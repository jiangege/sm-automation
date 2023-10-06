import html
import re
import base64
import pyperclip
import ctypes
import win32gui
import win32api
import win32process
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pywinauto import Application


class SuperMemoAutomation:
    def __init__(self, exe_path):
        self.exe_path = exe_path
        self.app = Application(backend='uia').connect(path=exe_path)
        self.telwind = self.app.window(class_name="TElWind")
        self.status = self.get_status()
        self.tscroll_box = self.telwind.window(class_name="TScrollBox")
        self.tstat_bar = self.app.window(class_name="TStatBar")
        self.is_prev_enabled = self.check_prev_enabled()
        self.is_next_enabled = self.check_next_enabled()

    def __send_command(self, type, menu_id):
        WM_COMMAND = 0x111

        def enum_windows_proc(hwnd, lparam):
            class_name = win32gui.GetClassName(hwnd)
            if class_name == 'TPUtilWindow':
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                process_handle = win32api.OpenProcess(
                    0x1000, False, pid)
                executable_path = win32process.GetModuleFileNameEx(
                    process_handle, 0)
                win32api.CloseHandle(process_handle)
                if executable_path.endswith(self.exe_path):
                    win32gui.SendMessage(hwnd, WM_COMMAND, menu_id, type)

        win32gui.EnumWindows(enum_windows_proc, None)

    def __parse_element(self, data):
        lines = data.split("\n")
        parsed_data = {}
        current_section = parsed_data
        section_stack = []

        for line in lines:
            if line.startswith("Begin "):
                section_name = line.split()[1]

                if section_name in current_section:
                    if not isinstance(current_section[section_name], list):
                        current_section[section_name] = [
                            current_section[section_name]]

                    current_section[section_name].append({})
                    section_stack.append(current_section)
                    current_section = current_section[section_name][-1]
                else:
                    current_section[section_name] = {}
                    section_stack.append(current_section)
                    current_section = current_section[section_name]
            elif line.startswith("End "):
                current_section = section_stack.pop()
            elif "=" in line:
                key, value = line.split("=", 1)
                current_section[key] = value

        return parsed_data

    def __continue_leech_alert(self):
        tleech_manager_dlg = self.app.window(class_name="TLeechManagerDlg")
        if tleech_manager_dlg.exists():
            tleech_manager_dlg.window(
                class_name="TBitBtn", title="Continue").click_input()

    def get_current_element_info(self):
        self.__send_command(type=1, menu_id=700)
        element_text = pyperclip.paste()
        element_data = self.__parse_element(element_text)['Element']

        def map_components():
            components = []
            if 'Component' not in element_data:
                return components
            ele_components = [element_data['Component']] if isinstance(
                element_data['Component'], dict) else element_data['Component']
            for component in ele_components:
                components.append({
                    "type": component.get('Type', '').strip(),
                    "text": component.get('Text', '').strip(),
                    "htm_file": component.get('HTMFile', '').strip(),
                    "htm_name": component.get('HTMName', '').strip(),
                    "image_file": component.get('ImageFile', '').strip(),
                    "image_name": component.get('ImageName', '').strip(),
                    "display_at": component.get('DisplayAt', '').strip(),
                })
            return components

        return {
            "type": element_data['ElementInfo']['Type'].strip(),
            "title": element_data['ElementInfo']['Title'].strip(),
            "parent_title": element_data['ParentTitle'].strip(),
            "status": element_data['ElementInfo']['Status'].strip(),
            "priority": float(element_data['Priority'].strip()),
            "lapses": int(element_data['ElementInfo']['Lapses'].strip()),
            "last_repetition": datetime.strptime(element_data['ElementInfo']['LastRepetition'].strip(), '%d.%m.%y'),
            "interval": int(element_data['ElementInfo']['Interval'].strip()),
            "reference": html.unescape(element_data['ElementInfo']['Reference'].strip()),
            "components": map_components()
        }

    def get_current_element(self):
        element_info = self.get_current_element_info()
        components = element_info['components']

        for component in components:
            if component['type'] == 'HTML':
                try:
                    if component['text']:
                        component['content'] = component['text']
                    with open(component['htm_file'], 'r') as file:
                        file_content = file.read()
                        unescaped_content = html.unescape(file_content)
                        component['content'] = unescaped_content
                except Exception as e:
                    print(e)
            elif component['type'] == 'Image':
                try:
                    with open(component['image_file'], "rb") as img_file:
                        base64_string = base64.b64encode(
                            img_file.read()).decode('utf-8')
                        component['content'] = f'<img src="data:image/png;base64,{base64_string}" />'
                except Exception as e:
                    print(e)

        self.current_element = element_info

        return element_info

    def set_html_content(self, htm_file, content):
        with open(htm_file, 'w') as file:
            file.write(content)

    def set_text_content(self, component_index, content):
        ie_server = self.tscroll_box.window(
            class_name="Internet Explorer_Server", found_index=component_index)

        ie_server.set_focus()
        ie_server.type_keys('^a')
        ie_server.type_keys('{BACKSPACE}')

        pyperclip.copy(content)

        # paste HTML
        self.__send_command(type=1, menu_id=843)

    def get_stat(self):

        outstanding_topics, outstanding_items, *rest = re.findall(
            r'\d+', self.tstat_bar.Pane3.window_text())

        memorized_items, memorized_topics = re.findall(
            r'\d+', self.tstat_bar.Pane4.window_text())

        return {
            'outstanding': {
                'topics':  int(outstanding_topics),
                'items': int(outstanding_items),
            },
            'memorized': {
                'topics': int(memorized_topics),
                'items': int(memorized_items)
            }
        }

    def set_priority(self, priority):
        t_priority_dlg = self.app.window(class_name="TPriorityDlg")
        if not t_priority_dlg.exists(timeout=1):
            ctypes.windll.user32.LoadKeyboardLayoutW('00000409', 1)
            self.telwind.set_focus()
            self.telwind.type_keys('%p')
            t_priority_dlg = self.app.window(class_name="TPriorityDlg")
        t_priority_dlg.Edit5.set_edit_text(priority)
        t_priority_dlg.OK.click_input()

    def dismiss(self):
        self.telwind.set_focus()
        self.telwind.type_keys('^d')
        tmsg_dialog = self.app.window(class_name="TMsgDialog")
        yes_btn = tmsg_dialog.Yes
        if yes_btn.exists():
            tmsg_dialog.Yes.click_input()
            tmsg_dialog.OK.click_input()

        ok_btn = tmsg_dialog.OK
        if ok_btn.exists():
            return tmsg_dialog.OK.click_input()

    def done(self):
        self.telwind.set_focus()
        self.telwind.type_keys('+^~')
        tmsg_dialog = self.app.window(class_name="TMsgDialog")
        yes_btn = tmsg_dialog.Yes
        if yes_btn.exists():
            tmsg_dialog.Yes.click_input()
            tmsg_dialog.Yes.click_input()

        ok_btn = tmsg_dialog.OK
        if ok_btn.exists():
            return tmsg_dialog.OK.click_input()

    def grade(self, grade):
        self.telwind.set_focus()
        show_answer_btn = self.telwind.window(
            class_name="TBitBtn", title="Show answer")
        if show_answer_btn.exists():
            show_answer_btn.click_input()
        self.telwind.window(class_name="TBitBtn", found_index=int(
            grade)).click_input()

    def cancel(self):
        self.telwind.set_focus()
        self.telwind.window(class_name="TBitBtn",
                            found_index=0).click_input()

    def next(self):
        self.telwind.set_focus()
        self.telwind.window(class_name="TBitBtn",
                            title="Next repetition",
                            control_btn="Button"
                            ).click_input()
        self.__continue_leech_alert()

    def show_answer(self):
        self.telwind.set_focus()
        self.telwind.window(
            class_name="TBitBtn", title="Show answer", control_btn="Button").click_input()

    def get_status(self):
        def check_exists(title):
            return self.telwind.window(class_name='TBitBtn', title=title, control_type="Button").exists()

        with ThreadPoolExecutor(max_workers=3) as executor:
            titles = ["Learn", "Show answer", "Next repetition"]
            results = list(executor.map(check_exists, titles))

        if results[0]:
            return 'learning'
        if results[1]:
            return 'show_answer'
        if results[2]:
            return 'next'

        return 'grade'

    def learn(self):
        self.telwind.set_focus()
        self.telwind.window(class_name='TBitBtn', title="Learn").click_input()
        self.__continue_leech_alert()

    def prev_element(self):
        self.telwind.set_focus()
        btn = self.telwind.window(control_type='Button', title="<")
        btn.click_input()
        self.is_prev_enabled = self.check_prev_enabled()
        self.is_next_enabled = self.check_next_enabled()

    def next_element(self):
        self.telwind.set_focus()
        btn = self.telwind.window(control_type='Button', title=">")
        btn.click_input()
        self.is_prev_enabled = self.check_prev_enabled()
        self.is_next_enabled = self.check_next_enabled()

    def check_prev_enabled(self):
        btn = self.telwind.window(control_type='Button', title="<")
        return btn.is_enabled()

    def check_next_enabled(self):
        btn = self.telwind.window(control_type='Button', title=">")
        return btn.is_enabled()
