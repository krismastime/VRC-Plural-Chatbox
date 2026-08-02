# Version 0.1 VRC-Plural-Chatbox by Krismastime
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
    QDialogButtonBox,
    QSizePolicy
)
from PyQt6.QtGui import QColor, QPalette

class Program():
    def __init__(self):
        super().__init__()

    def vrchat_plural_start(self,chatbox_preview,logger):
        vrchat_plural_library.taskcancelled = False
        save_data()
        Program.loop = asyncio.new_event_loop()
        self.loop.run_until_complete(vrchat_plural_library.main(load_settings(0),chatbox_preview,logger))

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
    chatboxlg = pyqtSignal(str)
    logger = pyqtSignal(str)

class Worker(QRunnable):

    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
        self.thread_id = kwargs.get("thread_id", 0)
        self.kwargs["chatbox_preview"] = self.signals.chatboxlg
        self.kwargs["logger"] = self.signals.logger
        self.is_running = True

    @pyqtSlot()
    def run(self):
        while self.is_running:
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

    def stop(self):
        self.is_running = False


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

        try:
            member_widget.memberdict = s["memberdict"]
        except:
            if "generating" in tb:
                dlg = CustomDialog(message="Unable to parse settings.json or file does not exist. Generating...")
                dlg.exec()
                sys.exit()

        member_widget.fronters = []
        member_widget.frontinfo = {}

        member_widget.layoutall = QVBoxLayout()
        member_widget.columns = QHBoxLayout()

        member_widget.id = QVBoxLayout()
        member_widget.pronouns = QVBoxLayout()
        member_widget.avatar = QVBoxLayout()
        member_widget.front = QVBoxLayout()
        member_widget.deleteBtn = QVBoxLayout()

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

        for i in reversed(range(self.id.count())):
            self.id.itemAt(i).widget().setParent(None)
            self.pronouns.itemAt(i).widget().setParent(None)
            self.avatar.itemAt(i).widget().setParent(None)
            self.front.itemAt(i).widget().setParent(None)
            self.deleteBtn.itemAt(i).widget().setParent(None)

        for i in self.columns.children():
            self.columns.removeItem(i)

        self.id.setSpacing(0)
        id_label = QLabel(text="Name")
        self.id.addWidget(id_label)
        
        self.pronouns.setSpacing(0)
        pronouns_label = QLabel(text="Pronouns")
        self.pronouns.addWidget(pronouns_label)

        self.front.setSpacing(0)
        front_label = QLabel(text="Fronting")
        self.front.addWidget(front_label)

        self.deleteBtn.setSpacing(0)
        delete_label = QLabel(text="Delete")
        self.deleteBtn.addWidget(delete_label)

        self.avatar.setSpacing(0)
        avatar_label = QLabel(text="Avatar ID")
        self.avatar.addWidget(avatar_label)

        member_widget.id_boxes = []
        member_widget.pronouns_boxes = []
        member_widget.avatar_boxes = []
        member_widget.member_number = []
        member_widget.front_boxes = []
        member_widget.delete_boxes = []

        #member_widget.memberdict = memberdict
        a = 0

        for i in self.memberdict:
            if i != "name":
                self.id_boxes.append(QLabel(text=i))
                self.pronouns_boxes.append(QLabel(text=self.memberdict[i]["pronouns"]))
                self.avatar_boxes.append(QLineEdit(text=self.memberdict[i]["avatar"]))
                temp = QPushButton(text="✗")
                temp.setEnabled(False)
                self.front_boxes.append(temp) ##↑↓
                self.delete_boxes.append(QPushButton(text="🗑"))
                self.member_number.append(a)
                a += 1
                
        
        for i in range(len(self.id_boxes)):
            self.id.addWidget(self.id_boxes[i])
            self.pronouns.addWidget(self.pronouns_boxes[i])
            self.avatar.addWidget(self.avatar_boxes[i])

            self.front.addWidget(self.front_boxes[i])
            self.deleteBtn.addWidget(self.delete_boxes[i])

        for widget in self.member_number:
            try:
                self.front_boxes[widget].setCheckable(True)
                self.connect_front(self.front_boxes[widget],widget)
                self.connect_delete(self.delete_boxes[widget],widget)
            except:
                continue

        self.columns.addLayout(self.id)
        self.columns.addLayout(self.pronouns)
        self.columns.addLayout(self.avatar)
        self.columns.addLayout(self.front)
        self.columns.addLayout(self.deleteBtn)

        self.setLayout(self.layoutall)
    
    def connect_front(self, widget,num):
        widget.clicked.connect(lambda: self.front_toggle(num))

    def connect_delete(self,widget,num):
        widget.clicked.connect(lambda: self.delete_member(num))

    def front_toggle(self,i):
        if self.front.itemAt(i+1).widget().text() == "✗":
            self.front.itemAt(i+1).widget().setText("✓")
            self.fronters.append(str(self.id.itemAt(i+1).widget().text()))
        else:
            self.front.itemAt(i+1).widget().setText("✗")
            self.fronters.remove(str(self.id.itemAt(i+1).widget().text()))
            try:
                self.frontinfo.pop(str(self.id.itemAt(i+1).widget().text()))
            except Exception as e:
                start_options.traceback.setText("Already removed from front.")
        for i in self.fronters:
            self.frontinfo[i] = {"pronouns":self.memberdict[i]["pronouns"],"avatar":self.memberdict[i]["avatar"]}
        asyncio.run(vrchat_plural_library.fronter_format(self.frontinfo))
        return
    
    def delete_member(self,i):
        self.memberdict.pop(str(self.id.itemAt(i+1).widget().text()))
        self.list_members()

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

class chatbox_widget(QWidget):
    def __init__(self):
        super().__init__()

        s, tb = load_settings(x=2)
        chatbox_widget.cbx_types = s["chatboxes"]

        chatbox_widget.cbx_activecontent = ""

        chatbox_widget.layoutall = QVBoxLayout()
        chatbox_widget.columns = QHBoxLayout()

        chatbox_widget.cbx_names = QVBoxLayout()
        chatbox_widget.cbx_content = QVBoxLayout()
        chatbox_widget.cbx_active = QVBoxLayout()
        chatbox_widget.deleteBtn = QVBoxLayout()

        chatbox_widget.newCbx = QHBoxLayout()

        chatbox_widget.newCbxName = QLineEdit()
        self.newCbxName.setPlaceholderText("Chatbox Name")
        self.newCbxName.setMinimumHeight(50)
        self.newCbx.addWidget(self.newCbxName)
        chatbox_widget.newContent = QTextEdit()
        self.newContent.setPlaceholderText("Chatbox Text")
        self.newContent.setSizePolicy(QSizePolicy.Policy.Fixed,QSizePolicy.Policy.Expanding)
        self.newContent.setMaximumHeight(50)
        self.newCbx.addWidget(self.newContent)
        

        chatbox_widget.addCbx = QPushButton(text="Add Chatbox")
        self.addCbx.clicked.connect(self.add_member)

        self.columns.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layoutall.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.layoutall.addWidget(self.addCbx)
        self.layoutall.addLayout(self.newCbx)
        self.layoutall.addLayout(self.columns)
        self.setLayout(self.layoutall)
        self.list_members()

    def add_member(self):
        alert = QDialog()
        if len(self.newCbxName.text()) < 1:
            dlg = CustomDialog(message="Chatbox name cannot be empty")
            dlg.exec()
            return

        self.cbx_types[self.newCbxName.text()] = self.newContent.toPlainText()

        print(self.cbx_types)
        self.newCbxName.setText("")
        self.newContent.setText("")
        self.list_members() #keeps layering everything on top of itself
        return

    def list_members(self):

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

        for i in reversed(range(self.cbx_names.count())):
            self.cbx_names.itemAt(i).widget().setParent(None)
            self.cbx_content.itemAt(i).widget().setParent(None)
            self.cbx_active.itemAt(i).widget().setParent(None)
            self.deleteBtn.itemAt(i).widget().setParent(None)

        for i in self.columns.children():
            self.columns.removeItem(i)

        self.cbx_names.setSpacing(0)
        id_label = QLabel(text="Chatbox")
        self.cbx_names.addWidget(id_label)
        
        self.cbx_content.setSpacing(0)
        pronouns_label = QLabel(text="Content")
        self.cbx_content.addWidget(pronouns_label)

        self.cbx_active.setSpacing(0)
        front_label = QLabel(text="Visible")
        self.cbx_active.addWidget(front_label)

        self.deleteBtn.setSpacing(0)
        delete_label = QLabel(text="Delete")
        self.deleteBtn.addWidget(delete_label)

        chatbox_widget.cbxNameBoxes = []
        chatbox_widget.cbxContentBoxes = []
        chatbox_widget.cbxNumber = []
        chatbox_widget.cbxActiveButtons = []
        chatbox_widget.cbxDeleteButtons = []

        #chatbox_widget.memberdict = memberdict
        a = 0

        for i in self.cbx_types:
            if i != "name":
                self.cbxNameBoxes.append(QLabel(text=i))
                tempcontent = QTextEdit()
                tempcontent.setPlainText(self.cbx_types[i])
                tempcontent.setReadOnly(True)
                tempcontent.setMaximumHeight(50)
                self.cbxContentBoxes.append(tempcontent)
                tempbutton = QPushButton(text="✗")
                self.cbxActiveButtons.append(tempbutton) ##↑↓
                self.cbxDeleteButtons.append(QPushButton(text="🗑"))
                self.cbxNumber.append(a)
                a += 1
                
        
        for i in range(len(self.cbxNameBoxes)):
            self.cbx_names.addWidget(self.cbxNameBoxes[i])
            self.cbx_content.addWidget(self.cbxContentBoxes[i])

            self.cbx_active.addWidget(self.cbxActiveButtons[i])
            self.deleteBtn.addWidget(self.cbxDeleteButtons[i])

        for widget in self.cbxNumber:
            try:
                self.cbxActiveButtons[widget].setCheckable(False)
                self.connect_front(self.cbxActiveButtons[widget],widget)
                self.connect_delete(self.cbxDeleteButtons[widget],widget)
            except:
                continue

        self.columns.addLayout(self.cbx_names)
        self.columns.addLayout(self.cbx_content)
        self.columns.addLayout(self.cbx_active)
        self.columns.addLayout(self.deleteBtn)

        self.setLayout(self.layoutall)
    
    def connect_front(self, widget,num):
        widget.clicked.connect(lambda: self.front_toggle(num))

    def connect_delete(self,widget,num):
        widget.clicked.connect(lambda: self.delete_member(num))

    def front_toggle(self,i):
        for a in self.cbxActiveButtons:
            if a != self.cbx_active.itemAt(i+1).widget():
                a.setText("✗")
        if self.cbx_active.itemAt(i+1).widget().text() == "✗":
            self.cbx_active.itemAt(i+1).widget().setText("✓")
            self.cbx_activecontent = str(self.cbx_content.itemAt(i+1).widget().toPlainText())
        else:
            self.cbx_active.itemAt(i+1).widget().setText("✗")
            try:
                self.cbx_activecontent = ""
            except Exception as e:
                start_options.traceback.setText("Already removed from front.")
        vrchat_plural_library.chatbox_format(self.cbx_activecontent)
        return
    
    def delete_member(self,i):
        self.cbx_types.pop(str(self.cbx_names.itemAt(i+1).widget().text()))
        self.list_members()

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
        self.startBtn.setEnabled(True)
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

            if int(member_widget.columns.count()) < 1:
                start_options.traceback.setText("Member list cannot be empty, gather members first.")
                self.startBtn.setChecked(False)
                for i in member_widget.front_boxes:
                    i.setEnabled(False)
            else:
                self.startBtn.setText("Stop")
                self.start()
                for i in member_widget.front_boxes:
                    i.setEnabled(True)
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

    def start(self):
        program = Program()
        start_options.startup = Worker(program.vrchat_plural_start)
        self.startup.signals.chatboxlg.connect(program.chatbox_fn)
        self.startup.signals.logger.connect(program.logging_fn)
        MainWindow.threadpool.start(self.startup)

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

        #layout.addWidget(login_widget(),0,0,alignment=Qt.AlignmentFlag.AlignTop)
        layout.addWidget(QLabel(text="Status updating coming in future update!"),0,0,alignment=Qt.AlignmentFlag.AlignTop)
        layout.addWidget(output_log(),2,0,alignment=Qt.AlignmentFlag.AlignTop)
        layout.addWidget(start_options(),3,0,alignment=Qt.AlignmentFlag.AlignBottom)

        layout.addWidget(member_widget(),0,1,alignment=Qt.AlignmentFlag.AlignTop)
        layout.addWidget(chatbox_preview(),2,1,alignment=Qt.AlignmentFlag.AlignTop)
        layout.addWidget(chatbox_widget(),1,1,alignment=Qt.AlignmentFlag.AlignBottom)
        layout.addWidget(self.ping,3,1,alignment=Qt.AlignmentFlag.AlignBottom)

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

    def closeEvent(self, event):
        output_log.log.setPlainText("Closing Application.")
        try:
            vrchat_plural_library.taskcancelled = True
            start_options.startup.stop()
            self.threadpool.waitForDone()
        except:
            pass
        event.accept()


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
    collection = {
        "auths":auths,
        "memberdict": member_widget.memberdict,
        "chatboxes":chatbox_widget.cbx_types
        }

    with open("settings.json","w") as file:
        json.dump(collection,file,indent=4)
    start_options.traceback.setText("Saved!")

app = QApplication(sys.argv)

window = MainWindow()
window.show()

sys.exit(app.exec())