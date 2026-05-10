# This file is used for experimental ui features
# I dont know anything about graphical interfaces when it comes to programming so if there are any issues let me know
import sys, json, vrchat_plural_library, asyncio, http.client, queue, time, traceback
from PyQt6.QtCore import (
    QSize,
    Qt,
    QRunnable,
    QThreadPool,
    QTimer,
    QObject,
    pyqtSlot,
    pyqtSignal
)
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QPushButton,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QCheckBox,
    QLabel,
    QComboBox,
    QTextEdit,
    QLineEdit,
    QTextBrowser,
    QGridLayout,
    QInputDialog,
    QDialog,
    QDialogButtonBox
)
from PyQt6.QtGui import QColor, QPalette

class Program():
    def __init__(self):
        super().__init__()

    def vrchat_plural_start(self,chatbox_preview,logger):
        vrchat_plural_library.taskcancelled = False
        save_data()
        loop = asyncio.new_event_loop()
        loop.run_until_complete(vrchat_plural_library.auth(load_settings(0),chatbox_preview,logger))

    def chatbox_fn(self, data):
        chatbox_preview.preview.setPlainText(data)
    
    def logging_fn(self, data):
        if "Ping-" in data:
            data = data.replace("Ping-ponged:","")
            MainWindow.ping.setText(str("Ping |"+data))
        else:
            log_prev = str(output_log.log.toPlainText()+"\n"+data)
            output_log.log.setPlainText(log_prev)

class WorkerSignals(QObject):
    finished = pyqtSignal(int)
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)
    chatbox = pyqtSignal(str)
    logger = pyqtSignal(str)

class Worker(QRunnable):

    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
        self.thread_id = kwargs.get("thread_id", 0)
        self.kwargs["chatbox_preview"] = self.signals.chatbox
        self.kwargs["logger"] = self.signals.logger

    @pyqtSlot()
    def run(self):
        try:
            result = self.fn(*self.args,**self.kwargs)
        except Exception:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)
        finally:
            self.signals.finished.emit(self.thread_id)


class login_widget(QWidget):
    def __init__(self):
        super().__init__()
        login_widget.tb = ""
        layout = QVBoxLayout()
        login_widget.token = QLineEdit()
        self.token.setEchoMode(QLineEdit.EchoMode.Password)
        login_widget.status = QCheckBox(text="Enable Status Updating")
        
        login_widget.userid = QLineEdit()
        login_widget.user = QLineEdit()
        login_widget.passw = QLineEdit()
        self.passw.setEchoMode(QLineEdit.EchoMode.Password)
        login_widget.loginBtn = QPushButton(text="Log in")
        self.loginBtn.setEnabled(False)
        self.loginBtn.pressed.connect(self.login)

        self.passw.textChanged.connect(self.login_button_active)
        self.user.textChanged.connect(self.login_button_active)
        self.status.checkStateChanged.connect(self.status_active)

        login_widget.widgets = [self.user,self.passw,self.userid,self.status]

        layout.addWidget(self.status)
        layout.addWidget(QLabel(text="VRChat UserID"))
        layout.addWidget(self.userid)
        layout.addWidget(QLabel(text="VRChat Username or Email"))
        layout.addWidget(self.user)
        layout.addWidget(QLabel(text="VRChat Password"))
        layout.addWidget(self.passw)
        layout.addWidget(self.loginBtn)
        self.status_active()
        self.setLayout(layout)
    
    def status_active(self):
        if self.status.isChecked():
            self.user.setEnabled(True)
            self.passw.setEnabled(True)
            self.userid.setEnabled(True)
            self.login_button_active()
        else:
            self.user.setEnabled(False)
            self.passw.setEnabled(False)
            self.userid.setEnabled(False)
            self.loginBtn.setEnabled(False)

    def login_button_active(self):
        if len(self.user.text()) == 0 or len(self.passw.text()) == 0:
            self.loginBtn.setEnabled(False)
        else:
            self.loginBtn.setEnabled(True)
    
    def authorise(self,authcode):
        try:
            if "Email" in vrchat_plural_library.vrc_login.status:
                user = vrchat_plural_library.vrc_login.two_fa(0,authcode)
            elif "Two-Factor" in vrchat_plural_library.vrc_login.status:
                user = vrchat_plural_library.vrc_login.two_fa(1,authcode)
            return user
        
        except:
            return None
    
    def login(self):
        username = self.user.text()
        password = self.passw.text()
        login_widget.user = vrchat_plural_library.vrc_login.getauthfromfile(username,password)

        if "requested" in str(login_widget.user):
            start_options.traceback.setText(login_widget.user)
            login_widget.user = self.auth_box()

        elif "Unable" in str(login_widget.user):
            start_options.traceback.setText(login_widget.user)
            return
        
        if login_widget.user != None:
            start_options.traceback.setText("Logged in as "+login_widget.user.display_name)
        else:
            start_options.traceback.setText("Unable to log in")

    def auth_box(self):
        dialogue = QInputDialog()
        dialogue.setLabelText("Enter authentication code")
        dialogue.setWindowTitle("Authentication")

        clickedButton = dialogue.exec()

        user = None
        if clickedButton and len(dialogue.textValue()) > 0:
            user = self.authorise(dialogue.textValue())
        elif clickedButton and len(dialogue.textValue()) == 0:
            start_options.traceback.setText("Unable to log in, no authcode inputted")
        else:
            start_options.traceback.setText("Unable to log in, cancelled by user")
        
        return user

class CustomDialog(QDialog):
    def __init__(self,message="Error"):
        super().__init__()

        self.setWindowTitle("VRChat Pural Chatbox")

        QBtn = QDialogButtonBox.StandardButton.Ok

        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)


        layout = QVBoxLayout()
        QMessage = QLabel(message)
        layout.addWidget(QMessage)
        layout.addWidget(self.buttonBox)
        self.setLayout(layout)

class member_widget(QWidget):
    def __init__(self):
        super().__init__()

        s, tb = load_settings(x=2)
        member_widget.memberdict = s["memberdict"]

        member_widget.layoutall = QVBoxLayout()
        member_widget.columns = QHBoxLayout()

        member_widget.newMember = QHBoxLayout()

        member_widget.newName = QLineEdit()
        self.newName.setPlaceholderText("Name")
        self.newMember.addWidget(self.newName)
        member_widget.newPronouns = QLineEdit()
        self.newPronouns.setPlaceholderText("Pronouns")
        self.newMember.addWidget(self.newPronouns)
        member_widget.newAvatarID = QLineEdit()
        self.newAvatarID.setPlaceholderText("Avatar ID")
        self.newMember.addWidget(self.newAvatarID)
        

        member_widget.addMember = QPushButton(text="Add Member")
        self.addMember.clicked.connect(self.add_member)

        self.columns.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layoutall.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.layoutall.addWidget(self.addMember)
        self.layoutall.addLayout(self.newMember)
        self.layoutall.addLayout(self.columns)
        self.setLayout(self.layoutall)
        self.list_members()

    def add_member(self):
        alert = QDialog()
        if len(self.newName.text()) < 1:
            dlg = CustomDialog(message="Member name cannot be empty")
            dlg.exec()
            return

        self.memberdict[self.newName.text()] = {"avatar":self.newAvatarID.text(),"pronouns":self.newPronouns.text()}

        print(self.memberdict)
        self.newName.setText("")
        self.newPronouns.setText("")
        self.newAvatarID.setText("")
        self.list_members() #keeps layering everything on top of itself
        return

    def list_members(self):

        columns = self.columns
        for i in columns.children():
            columns.removeItem(i)

        # for i in memberdict:
        #     if i in settings["memberdict"]:
        #         print(memberdict[i][1])
        #         if memberdict[i][1] != settings["memberdict"][i]["pronouns"]:
        #             settings["memberdict"][i]["pronouns"] = memberdict[i][1]
        #     else:
        #         settings["memberdict"][i] = {
        #             "name":memberdict[i][0],
        #             "avatar":"",
        #             "pronouns":memberdict[i][1]
        #             }
        
        id = QVBoxLayout()
        pronouns = QVBoxLayout()
        avatar = QVBoxLayout()
        front = QVBoxLayout()

        for i in id.children():
            id.removeItem(i)
        for i in pronouns.children():
            pronouns.removeItem(i)
        for i in avatar.children():
            avatar.removeItem(i)
        
        id.setSpacing(0)
        id_label = QLabel(text="Name")
        id.addWidget(id_label)
        
        pronouns.setSpacing(0)
        pronouns_label = QLabel(text="Pronouns")
        pronouns.addWidget(pronouns_label)

        front.setSpacing(0)
        front_label = QLabel(text="Fronting")
        front.addWidget(front_label)

        avatar.setSpacing(0)
        avatar_label = QLabel(text="Avatar ID")
        avatar.addWidget(avatar_label)
        member_widget.id_boxes = []
        member_widget.pronouns_boxes = []
        member_widget.avatar_boxes = []
        member_widget.front_boxes = []
        #member_widget.memberdict = memberdict

        for i in self.memberdict:
            if i != "name":
                member_widget.id_boxes.append(QLabel(text=i))
                member_widget.pronouns_boxes.append(QLabel(text=self.memberdict[i]["pronouns"]))
                member_widget.avatar_boxes.append(QLineEdit(text=self.memberdict[i]["avatar"]))
                member_widget.front_boxes.append(QPushButton(text="↑")) ##↑↓
                
        
        for i in range(len(member_widget.id_boxes)):
            id.addWidget(member_widget.id_boxes[i])
            pronouns.addWidget(member_widget.pronouns_boxes[i])
            avatar.addWidget(member_widget.avatar_boxes[i])
            self.front_boxes[i].clicked.connect(self.front_toggle)
            front.addWidget(member_widget.front_boxes[i])


        columns.addLayout(id)
        columns.addLayout(pronouns)
        columns.addLayout(avatar)
        columns.addLayout(front)

        self.setLayout(self.layoutall)
        
    def front_toggle(self,i):
        print(self.id_boxes[i].text())
        if self.front_boxes[i].text() == "↑":
            self.front_boxes[i].setText("↓")
        else:
            self.front_boxes[i].setText("↑")
        return

class chatbox_preview(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()
        label = QLabel(text="Preview")

        chatbox_preview.preview = QTextBrowser()
        self.preview.setPlainText("Not Connected")

        layout.addWidget(label)
        layout.addWidget(self.preview)
        self.setLayout(layout)   
         
class output_log(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()
        label = QLabel(text="Log")

        output_log.log = QTextBrowser()

        layout.addWidget(label)
        layout.addWidget(self.log)
        self.setLayout(layout) 

class options_widget(QWidget):
    def __init__(self):
        super().__init__()
        
        layout = QVBoxLayout()

        visibleOnStart = QCheckBox(text="Chatbox Visible by Default")
        generic = QTextEdit()
        time_digital = QTextEdit()
        time_full = QTextEdit()
        afk = QTextEdit()
        status = QTextEdit()

        options_widget.widgets = [visibleOnStart,generic,time_digital,time_full,afk,status]

        layout.addWidget(QLabel(text="Default Chatbox"))
        layout.addWidget(generic)
        layout.addWidget(QLabel(text="Short Time"))
        layout.addWidget(time_digital)
        layout.addWidget(QLabel(text="Long Time"))
        layout.addWidget(time_full)
        layout.addWidget(QLabel(text="Away Message"))
        layout.addWidget(afk)
        layout.addWidget(QLabel(text="Status Message (if logged in)"))
        layout.addWidget(status)
        layout.addWidget(visibleOnStart)
        self.setLayout(layout)

class start_options(QWidget):
    def __init__(self,parent=None):
        super().__init__(parent)
        
        start_options.startBtn = QPushButton("Start",self)
        self.startBtn.setCheckable(True)
        self.startBtn.setEnabled(False)
        self.startBtn.clicked.connect(self.start_button)
        self.reloadBtn = QPushButton("Import Settings",self)
        self.reloadBtn.clicked.connect(self.reload_button)
        self.saveBtn = QPushButton("Save Settings",self) #Make it so you cannot save before members have been gathered
        self.saveBtn.clicked.connect(self.save_button)
        self.resetBtn = QPushButton("Reset Settings",self)
        self.resetBtn.clicked.connect(self.reset_button)

        layout = QVBoxLayout()

        layouttop = QHBoxLayout()
        layouttop.addWidget(self.startBtn)
        layouttop.addWidget(self.reloadBtn)
        layouttop.addWidget(self.saveBtn)
        layouttop.addWidget(self.resetBtn)

        self.traceback = QLabel("")
        start_options.traceback = self.traceback

        layout.addWidget(self.traceback)
        layout.addLayout(layouttop)
        self.setLayout(layout)
    
    def start_button(self):
        if self.startBtn.isChecked():

            if int(member_widget.columns.count()) < 3:
                start_options.traceback.setText("Member list cannot be empty, gather members first.")
                self.startBtn.setChecked(False)
            else:
                self.startBtn.setText("Stop")
                MainWindow.start()
        else:
            self.startBtn.setText("Start")
            chatbox_preview.preview.setPlainText("Not Connected")
            vrchat_plural_library.set_keybinds.cancel()
            vrchat_plural_library.taskcancelled = True

    def reload_button(self):
        try:
            settings, tracebackText = load_settings(2)
            self.traceback.setText(tracebackText)
        except Exception as e:
            self.traceback.setText("Unable to read or generate settings")
            print(e)
    
    def save_button(self):
        try:
            save_data()
        except:
            self.traceback.setText("Unable to save to settings")
    
    def reset_button(self):
        with open("settings.json","w") as file:
            file.write("")
        load_settings(2)
        self.traceback.setText("Reset settings to defaults")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("VRChat Plural Chatbox")
        self.setMinimumSize(QSize(500,500))
        self.setBaseSize(QSize(2000,600))

        MainWindow.threadpool = QThreadPool()

        MainWindow.ping = QLabel()

        self.draw_layout()


    def draw_layout(self):
        layout = QGridLayout()

        layout.addWidget(login_widget(),0,0,alignment=Qt.AlignmentFlag.AlignTop)
        layout.addWidget(output_log(),2,0,alignment=Qt.AlignmentFlag.AlignTop)
        layout.addWidget(start_options(),3,0,alignment=Qt.AlignmentFlag.AlignBottom)

        layout.addWidget(member_widget(),0,1,alignment=Qt.AlignmentFlag.AlignTop)
        layout.addWidget(chatbox_preview(),1,1,alignment=Qt.AlignmentFlag.AlignTop)
        layout.addWidget(options_widget(),2,1,alignment=Qt.AlignmentFlag.AlignBottom)
        layout.addWidget(self.ping,3,1,alignment=Qt.AlignmentFlag.AlignBottom)

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)


def getCheckboxState(state):
    if state == True:
        return 2
    else:
        return 0
    
def load_settings(x=0):
    tb, s = vrchat_plural_library.read_options_from_ui.get_options()
    if x == 0:
        return s
    elif x == 1:
        return tb
    elif x == 2:
        return s, tb
    else:
        return

def save_data():
    try:
        auths = vrchat_plural_library.vrc_login.auths
    except:
        with open("settings.json") as file:
            settings = json.load(file)
        auths = settings["auths"]
        temp_save = {
            }

        with open("settings.json","w") as file:
            json.dump(temp_save,file,indent=4)
        start_options.traceback.setText("Saved!")

app = QApplication(sys.argv)

window = MainWindow()
window.show()

app.exec()