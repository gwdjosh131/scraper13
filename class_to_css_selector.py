from constants import *

html_class = poster_info_class

html_class = html_class.split()

css_selector = '.' + '.'.join(html_class)
print(css_selector)
