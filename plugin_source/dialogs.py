
import aqt
import aqt.utils
import anki

import json
import requests

from aqt.qt import *
from aqt import mw

def get_local_deck_from_hash(input_hash):
    strings_data = mw.addonManager.getConfig(__name__)
    if strings_data:
        for hash, details in strings_data.items():
            if hash == input_hash:
                return mw.col.decks.name(details["deckId"])
    return "None"

def store_login_token(token):
    strings_data = mw.addonManager.getConfig(__name__)
    if strings_data:
        if "settings" not in strings_data:
            strings_data["settings"] = {}
        strings_data["settings"]["token"] = token
        strings_data["settings"]["auto_approve"] = False
    mw.addonManager.writeConfig(__name__, strings_data)
    

class ChangelogDialog(QDialog):
    def __init__(self, changelog, deck_hash):
        super().__init__()
        local_name = get_local_deck_from_hash(deck_hash)
        self.setWindowTitle(f"AnkiCollab - Changelog for Deck {local_name}")
        self.setModal(True)

        layout = QVBoxLayout()

        label = QLabel("The following changes are available:")
        layout.addWidget(label)

        changelog_text = QTextBrowser()
        
        if not changelog:
            changelog = "The maintainer left no changelog message for this update."
            
        changelog_text.setPlainText(changelog)
        layout.addWidget(changelog_text)

        button_box = QDialogButtonBox()
        install_button = button_box.addButton("Install Now", QDialogButtonBox.ButtonRole.AcceptRole)
        later_button = button_box.addButton("Decide Later", QDialogButtonBox.ButtonRole.RejectRole)
        skip_button = QPushButton("Skip this Update")
        button_box.addButton(skip_button, QDialogButtonBox.ButtonRole.ActionRole)

        layout.addWidget(button_box)

        self.setLayout(layout)

        install_button.clicked.connect(self.accept)
        later_button.clicked.connect(self.reject)
        skip_button.clicked.connect(self.skip_update)

        self.adjustSize()

    def skip_update(self):
        self.done(2)
        

class OptionalTagsDialog(QDialog):
    checkboxes = {}
    
    def __init__(self, old_tags, new_tags):
        super().__init__()
        layout = QVBoxLayout()

        self.setWindowTitle("AnkiCollab - Optional Tags")
        label = QLabel("You can subscribe to the following optional tags:")
        layout.addWidget(label)
        
        for item in new_tags:
            checkbox = QCheckBox(item)
            #set checked to the old value if it exists in the old tags, otherwise set it to false
            checkbox.setChecked(old_tags.get(item, False))
            self.checkboxes[item] = checkbox
            layout.addWidget(checkbox)

        button = QPushButton('Save')
        button.clicked.connect(lambda: self.close())
        layout.addWidget(button)

        self.setLayout(layout)
        self.show()

    def get_selected_tags(self):
        result = {}
        for item in self.checkboxes:
            result[item] = self.checkboxes[item].isChecked()

        return result
    
    
# Create a new Login Dialog that allows the user to enter their username and password
class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super(LoginDialog, self).__init__(parent)
        self.setWindowTitle("AnkiCollab - Login")
        self.setModal(True)
        self.resize(300, 100)

        layout = QVBoxLayout()

        label = QLabel("Please enter your AnkiCollab email and password:")
        layout.addWidget(label)

        form_layout = QFormLayout()

        self.email_input = QLineEdit()
        form_layout.addRow("Email:", self.email_input)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addRow("Password:", self.password_input)

        layout.addLayout(form_layout)

        button_box = QDialogButtonBox()
        login_button = button_box.addButton("Login", QDialogButtonBox.ButtonRole.AcceptRole)
        button_box.addButton("Cancel", QDialogButtonBox.ButtonRole.RejectRole)

        layout.addWidget(button_box)

        self.setLayout(layout)

        login_button.clicked.connect(self.login)

    def login(self):
        email = self.email_input.text()
        password = self.password_input.text()
        if not email or not password:
            aqt.mw.taskman.run_on_main(lambda: aqt.utils.showInfo("Please enter a email and password."))
            return
        
        payload = {
            'email': email,
            'password': password
        }
        response = requests.post("https://plugin.ankicollab.com/login", data=payload)

        if response.status_code == 200:
            res = response.text
            msg_box = QMessageBox()
            # if res is exactly 32 characters and no spaces, it's a token and we can assume it's a success
            if len(res) == 32 and " " not in res:
                store_login_token(res)
                msg_box.setText("Login successful!")
                self.done(0)
            else:
                msg_box.setText(res)
            msg_box.exec()
        else:
            aqt.mw.taskman.run_on_main(lambda: aqt.utils.showInfo("An error occurred while logging in. Please try again."))
            return
            
            