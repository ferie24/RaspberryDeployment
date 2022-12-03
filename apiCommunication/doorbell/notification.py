import os

#TODO: notification klasse worken
#TODO: IP Camera setup
#TODO: NOtification sound
#TODO: NAS script zum laufen bringen
class Notification:
    def __init__(self):
        pass

    def notify(self, title, text):
        os.system("""
                  osascript -e 'display notification "{}" with title "{}"'
                  """.format(text, title))
