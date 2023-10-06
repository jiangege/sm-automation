import threading
from sm_auto import SuperMemoAutomation

import pprint

pp = pprint.PrettyPrinter(indent=4)


sm = SuperMemoAutomation('sm19.exe')


# print(sm.get_html_contents())
# print(sm.get_stat())
# print(sm.get_current_element_priority())
# sm.set_current_element_priority(80)
# print(sm.get_current_element_priority())
# sm.cancel()
# sm.set_html_content(['q<h2>fuckyou</h2>', 'a'])


# print(sm.is_prev_enabled())

# current_element = sm.get_current_element()

# component1, *rest = current_element['components']

# sm.set_component_content(
#     htm_file=component1['htm_file'], content="test<b>你好 hello2</b>")

# sm.next()

# sm.grade(3)

# sm.next()

# print(sm.get_status())

# sm.show_answer()

# sm.set_current_element_priority(1)
# print(sm.get_current_element())

# pp.pprint(sm.get_current_element())


sm.set_text_content(1, 's<b>1</b>shit')
