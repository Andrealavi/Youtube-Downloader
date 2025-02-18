from tkinter import *
from tkinter import ttk
import time
import yt_dlp
from threading import Thread
import re
import mysql.connector
import os
import dotenv
import datetime


class AsyncDownload(Thread):
    def __init__(self, url, formatSelectionVar, downloadTitleLabel, downloadProgressBar, errorMessageLabel, user=None, videoHistory=None):
        super().__init__()

        self.url = url
        self.formatSelectionVar = formatSelectionVar.get()
        self.downloadTitleLabel = downloadTitleLabel
        self.progressBar = downloadProgressBar
        self.user = user
        self.videoHistory = videoHistory
        self.errorMessageLabel = errorMessageLabel

    def my_hook(self, d):
        if d['status'] == 'downloading':
            self.downloadTitleLabel['text'] = f"Downloading: {self.video_title}"
        elif d['status'] == 'finished':
            self.downloadTitleLabel['text'] = 'Download completed'

    def run(self):
        try:
            # Configure yt-dlp options
            ydl_opts = {
                'progress_hooks': [self.my_hook],
                'outtmpl': './Downloads/%(title)s.%(ext)s'
            }

            # Add format-specific options
            if self.formatSelectionVar == 'Audio':
                ydl_opts.update({
                    'format': 'bestaudio/best',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                    }],
                })
            elif self.formatSelectionVar == 'Video':
                ydl_opts.update({
                    'format': 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080]',  # Limit to 1080p
                })

            # Start progress bar
            progressBarThread = AsyncProgressBar(self.progressBar)
            progressBarThread.start()

            # Extract video information first
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.url.get(), download=False)
                self.video_title = info.get('title', None)
                video_length = info.get('duration', 0)

                # Update database if user is logged in
                if self.user is not None:
                    videoHistoryThread = AsyncDatabaseOperations('videoHistory', {
                        'title': self.video_title,
                        'length': video_length,
                        'link': self.url.get(),
                        'videoHistory': self.videoHistory
                    }, self.user[0])
                    videoHistoryThread.start()

                # Download the video
                ydl.download([self.url.get()])

            print(self.video_title)
            print(video_length)

            self.url.set('')

        except Exception as error:
            print(f"Error: {error}")  # For debugging
            self.errorMessageLabel.grid(column=0, columnspan=3, row=3)


class AsyncProgressBar(Thread):
    def __init__(self, progressBar):
        super().__init__()
        self.progressBar = progressBar

    def run(self):
        self.progressBar.grid(column=1, row=3, sticky=(S), pady=10)
        self.progressBar.start()


class AsyncDatabaseOperations(Thread):
    def __init__(self, operation, data, user):
        super().__init__()

        dotenv.load_dotenv()

        self.database = mysql.connector.connect(
            host=os.getenv('HOST'),
            user=os.getenv('USER'),
            password=os.getenv('PASSWORD'),
            database=os.getenv('DATABASE')
        )

        self.databaseCursor = self.database.cursor()
        self.data = data
        self.operation = operation
        self.user = user

    def addUser(self, email, password):
        statement = 'INSERT INTO Users (email, password) VALUES (%s, %s)'
        values = (email, password)

        regex = r"([a-zA-Z0-9_\-\.]+)@([a-zA-Z0-9_\-\.]+)\.([a-zA-Z]{2,5})"

        if not self.isUsed(email) and re.search(regex, email):
            self.databaseCursor.execute(statement, values)
            self.database.commit()

            self.fetchUser(self.data['email'], self.data['password'])
        else:
            self.data['errorMessageLabel']['text'] = 'This mail is already used, please insert another mail'

            if not re.search(regex, email):
                self.data['errorMessageLabel']['text'] = 'Please insert a correct value for the email field'

            self.data['errorMessageLabel'].grid(column=0, columnspan=2, row=4)
            time.sleep(2)

    def addVideoToVideoHistory(self, title, link, length, userId):
        statement = 'INSERT INTO VideoHistory (title, link, length, userId) VALUES (%s,%s,%s,%s)'
        values = (title, link, length, userId)

        self.databaseCursor.execute(statement, values)
        self.database.commit()

    def modifyUserInfo(self, email, password):
        statement = "UPDATE Users SET email = '{}', password = '{}' WHERE id = '{}'".format(
            email, password, self.user[0][0])

        regex = "([a-zA-Z0-9_\-\.]+)@([a-zA-Z0-9_\-\.]+)\.([a-zA-Z]{2,5})"

        if re.search(regex, email) and (not self.isUsed(email) or self.data['originalMail'] == email):
            self.databaseCursor.execute(statement)
            self.database.commit()

            self.fetchUser(email, password)
        else:
            self.data['errorMessageLabel']['text'] = 'This mail is already used, please insert another mail'

            if not re.search(regex, email):
                self.data['errorMessageLabel']['text'] = 'Please insert a correct value for the email field'

            self.data['errorMessageLabel'].grid(column=0, columnspan=2, row=3)
            time.sleep(2)

    def validateUser(self, email, password):
        statement = "SELECT * FROM Users WHERE email = '{}' and password = '{}'".format(
            email, password)

        regex = "([a-zA-Z0-9_\-\.]+)@([a-zA-Z0-9_\-\.]+)\.([a-zA-Z]{2,5})"

        if re.search(regex, email):
            self.database.commit()

            try:
                self.databaseCursor.execute(statement)
                result = self.databaseCursor.fetchall()[0]

                self.fetchUser(self.data['email'], self.data['password'])
            except:
                self.data['errorMessageLabel']['text'] = 'The mail or the password are not correct, please try again'
                self.data['errorMessageLabel'].grid(
                    column=0, columnspan=2, row=3)
                time.sleep(2)
        else:
            self.data['errorMessageLabel']['text'] = 'Please insert a correct value for the email field'
            self.data['errorMessageLabel'].grid(column=0, columnspan=2, row=3)
            time.sleep(2)

    def isUsed(self, email):
        statement = "SELECT * FROM Users WHERE email = '{}'".format(
            email)

        self.databaseCursor.execute(statement)

        result = self.databaseCursor.fetchall()

        if len(result) > 0:
            return True

    def fetchUser(self, email, password):
        statement = "SELECT * FROM Users WHERE email = '{}' and password = '{}'".format(
            email, password)

        self.databaseCursor.execute(statement)
        result = self.databaseCursor.fetchall()[0]

        self.fetchVideos(result[0])

        self.user.clear()

        self.user.append(result)

        self.database.commit()

    def fetchVideos(self, userId):
        statement = "SELECT * FROM VideoHistory WHERE userId = '{}'".format(
            userId)

        self.databaseCursor.execute(statement)
        videos = self.databaseCursor.fetchall()

        self.data['videoHistory'].clear()

        for video in videos:
            self.data['videoHistory'].append(video)

        self.database.commit()

    def run(self):
        if self.operation == 'signin':
            self.addUser(self.data['email'], self.data['password'])
        elif self.operation == 'login':
            if self.validateUser(self.data['email'], self.data['password']):
                self.user.append(self.fetchUser(
                    self.data['email'], self.data['password']))
        elif self.operation == 'videoHistory':
            self.addVideoToVideoHistory(
                self.data['title'], self.data['link'], self.data['length'], self.user[0])
            self.fetchVideos(self.user[0])
        elif self.operation == 'modifyAccountInfo':
            self.modifyUserInfo(self.data['email'], self.data['password'])


class YoutubeDownloader:
    def __init__(self, App):
        self.App = App
        self.App.title('Youtube Downloader')

        self.mainFrame = ttk.Frame(App, padding=(25, 0, 25, 25))

        self.user = []
        self.videoHistory = []

        # Try to load app icon, continue without if not found
        try:
            appIcon = PhotoImage(file="./data/AppIcon.png")
            self.App.iconphoto(False, appIcon)
        except:
            pass

        self.mainFrame.grid(column=0, row=0, sticky=(N, S, E, W))

        self.downloadPage()

    def topMenu(self, page=''):
        self.App.option_add('*tearOff', FALSE)

        self.menuBar = Menu(self.App)
        self.App['menu'] = self.menuBar
        self.menuUser = Menu(self.menuBar)

        if self.user != []:
            self.menuBar.add_cascade(menu=self.menuUser, label=self.user[0][1])
            self.menuUser.add_command(
                label='View Download History', command=self.videoHistoryPage)
            self.menuUser.add_command(
                label='View Account Info', command=self.accountInfoPage)
        elif page == 'videoHistory' or page == 'accountInfo' or page == 'modifyAccountInfo':
            self.menuBar.add_command(
                label='Download', command=self.downloadPage)
        elif page == 'signin':
            self.menuBar.add_command(
                label='Download', command=self.downloadPage)
            self.menuBar.add_command(
                label='Log in', command=self.loginPage)
        elif page == 'login':
            self.menuBar.add_command(
                label='Download', command=self.downloadPage)
            self.menuBar.add_command(
                label='Sign in', command=self.signinPage)
        else:
            self.menuBar.add_cascade(menu=self.menuUser, label='User')
            self.menuUser.add_command(label='Sign in', command=self.signinPage)
            self.menuUser.add_command(label='Log in', command=self.loginPage)

    def downloadPage(self):
        self.clearFrame()
        self.topMenu()

        # Create title label first
        self.titleLabel = ttk.Label(self.mainFrame, padding=(15, 15, 15, 15))

        # Try to load logo, use text if not found
        try:
            self.titleImage = PhotoImage(file="./data/AppLogo.png")
            self.titleLabel['image'] = self.titleImage
        except:
            self.titleLabel['text'] = "YouTube Downloader"
            self.titleLabel['font'] = ('Helvetica', 16, 'bold')

        self.url = StringVar()
        self.urlLabel = ttk.Label(
            self.mainFrame, text="URL:", padding=(0, 0, 15, 0), justify="right")
        self.urlEntry = ttk.Entry(self.mainFrame, textvariable=self.url)

        pasteVideoLinkButton = ttk.Button(
            self.mainFrame, text="Paste Link", command=lambda: self.pasteFromClipboard(self.url), padding=(1, 1, 1, 1))

        self.formatSelectionVar = StringVar()
        self.formatSelectionVar.set('Video')
        self.formatSelection = ttk.Combobox(
            self.mainFrame, textvariable=self.formatSelectionVar)
        self.formatSelection['value'] = ('Audio', 'Video')

        self.downloadButton = ttk.Button(
            self.mainFrame, text="Download", command=self.downloadHandler, padding=(1, 1, 1, 1))

        self.titleLabel.grid(column=1, row=0, sticky=(N))
        self.urlLabel.grid(column=0, row=1, sticky=(E, W))
        self.urlEntry.grid(column=1, row=1, sticky=(E, W))
        pasteVideoLinkButton.grid(column=2, row=1, padx=10)
        self.formatSelection.grid(column=3, row=1, sticky=(E, W), padx=10)
        self.downloadButton.grid(column=1, row=2, sticky=(S), pady=10)

        self.App.columnconfigure(0, weight=1)
        self.App.rowconfigure(0, weight=1)
        self.mainFrame.columnconfigure(0, weight=3)
        self.mainFrame.columnconfigure(1, weight=3)
        self.mainFrame.columnconfigure(2, weight=3)
        self.mainFrame.rowconfigure(0, weight=3)
        self.mainFrame.rowconfigure(1, weight=1)
        self.mainFrame.rowconfigure(2, weight=1)

        self.urlEntry.focus()

    def loginPage(self):
        self.clearFrame()
        self.topMenu('login')

        self.email = StringVar()
        emailLabel = ttk.Label(
            self.mainFrame, text="Email:", padding=(0, 0, 15, 0), justify="right")
        emailEntry = ttk.Entry(self.mainFrame, textvariable=self.email)

        self.password = StringVar()
        passwordLabel = ttk.Label(
            self.mainFrame, text="Password:", padding=(0, 0, 15, 0), justify="right")
        passwordEntry = ttk.Entry(
            self.mainFrame, textvariable=self.password, show='*')

        loginButton = ttk.Button(
            self.mainFrame, text="Log In", command=self.loginHandler, padding=(1, 1, 1, 1))

        self.errorMessageLabel = ttk.Label(
            self.mainFrame, padding=(10, 10, 10, 10))

        emailLabel.grid(column=0, row=0, sticky=(E, W))
        emailEntry.grid(column=1, row=0, sticky=(E, W), pady=10)
        passwordLabel.grid(column=0, row=1, sticky=(E, W))
        passwordEntry.grid(column=1, row=1, sticky=(E, W), pady=10)
        loginButton.grid(column=0, columnspan=2, row=2, sticky=(S), pady=10)

        emailEntry.focus()

    def signinPage(self):
        self.clearFrame()
        self.topMenu('signin')

        self.email = StringVar()
        emailLabel = ttk.Label(
            self.mainFrame, text="Email:", padding=(0, 0, 15, 0), justify="right")
        emailEntry = ttk.Entry(self.mainFrame, textvariable=self.email)

        self.password = StringVar()
        passwordLabel = ttk.Label(
            self.mainFrame, text="Password:", padding=(0, 0, 15, 0), justify="right")
        passwordEntry = ttk.Entry(
            self.mainFrame, textvariable=self.password, show='*')

        passwordValidation = StringVar()
        passwordValidationLabel = ttk.Label(
            self.mainFrame, text="Confirm your password:", padding=(0, 0, 15, 0), justify="right")
        passwordValidationEntry = ttk.Entry(
            self.mainFrame, textvariable=passwordValidation, show='*')

        signinButton = ttk.Button(
            self.mainFrame, text="Sign in", command=self.signinHandler, padding=(1, 1, 1, 1))

        self.errorMessageLabel = ttk.Label(
            self.mainFrame, padding=(10, 10, 10, 10))

        emailLabel.grid(column=0, row=0, sticky=(E, W))
        emailEntry.grid(column=1, row=0, sticky=(E, W), pady=10)
        passwordLabel.grid(column=0, row=1, sticky=(E, W))
        passwordValidationLabel.grid(column=0, row=2, sticky=(E, W))
        passwordEntry.grid(column=1, row=1, sticky=(E, W), pady=10)
        passwordValidationEntry.grid(column=1, row=2, sticky=(E, W), pady=10)
        signinButton.grid(column=0, columnspan=2, row=3, sticky=(S), pady=10)

        emailEntry.focus()

    def videoHistoryPage(self):
        i = 0

        self.clearFrame()
        self.topMenu('videoHistory')

        if self.videoHistory == []:
            noVideoLabel = ttk.Label(
                self.mainFrame, text="There are no downloaded video", padding=(25, 25, 25, 25))
            noVideoLabel.grid(column=0, row=0)
        else:
            for video in self.videoHistory:
                videoTitle = ttk.Label(
                    self.mainFrame, text=video[1], padding=(0, 0, 25, 10))
                videoLink = ttk.Label(
                    self.mainFrame, text=video[2], padding=(0, 0, 0, 10))
                copyVideoLinkButton = ttk.Button(
                    self.mainFrame, text='Copy Link', command=lambda j=i: self.copyToClipboard(self.videoHistory[j][2]), padding=(1, 1, 1, 1))
                videoLength = ttk.Label(self.mainFrame, text=str(
                    datetime.timedelta(seconds=int(video[3]))), padding=(25, 0, 0, 10))

                videoTitle.grid(column=0, row=i)
                videoLink.grid(column=1, columnspan=3, row=i)
                copyVideoLinkButton.grid(column=4, row=i, pady=10, padx=10)
                videoLength.grid(column=5, row=i)

                i += 1

    def accountInfoPage(self):
        self.clearFrame()
        self.topMenu('accountInfo')

        emailLabel = ttk.Label(
            self.mainFrame, text="Email:", padding=(0, 15, 15, 0), justify="right")
        emailValueLabel = ttk.Label(
            self.mainFrame, text=self.user[0][1], padding=(0, 15, 15, 0))

        passwordLabel = ttk.Label(
            self.mainFrame, text="Password:", padding=(0, 15, 15, 0), justify="right")
        passwordValueLabel = ttk.Label(
            self.mainFrame, text=''.join(['*' for char in self.user[0][2]]), padding=(0, 15, 15, 0))

        modifyAccountInfoButton = ttk.Button(
            self.mainFrame, text='Modify Information', command=self.modifyAccountInfo, padding=(1, 1, 1, 1))

        self.errorMessageLabel = ttk.Label(
            self.mainFrame, padding=(10, 10, 10, 10))

        emailLabel.grid(column=0, row=0)
        emailValueLabel.grid(column=1, columnspan=2, row=0)
        passwordLabel.grid(column=0, row=1)
        passwordValueLabel.grid(column=1, columnspan=2, row=1)
        modifyAccountInfoButton.grid(column=0, columnspan=2, row=2, pady=10)

    def modifyAccountInfo(self):
        self.clearFrame()
        self.topMenu('modifyAccountInfo')

        self.email = StringVar()
        self.email.set(self.user[0][1])
        emailLabel = ttk.Label(
            self.mainFrame, text="Email:", padding=(0, 0, 15, 0), justify="right")
        emailEntry = ttk.Entry(self.mainFrame, textvariable=self.email)

        self.password = StringVar()
        self.password.set(self.user[0][2])
        passwordLabel = ttk.Label(
            self.mainFrame, text="Password:", padding=(0, 0, 15, 0), justify="right")
        passwordEntry = ttk.Entry(
            self.mainFrame, textvariable=self.password, show='*')

        passwordValidation = StringVar()
        passwordValidationLabel = ttk.Label(
            self.mainFrame, text="Confirm your password:", padding=(0, 0, 15, 0), justify="right")
        passwordValidationEntry = ttk.Entry(
            self.mainFrame, textvariable=passwordValidation, show='*')

        modifyInfoButton = ttk.Button(
            self.mainFrame, text="Save Changes", command=self.modifyAccountInfoHandler, padding=(1, 1, 1, 1))

        self.errorMessageLabel = ttk.Label(
            self.mainFrame, padding=(10, 10, 10, 10))

        emailLabel.grid(column=0, row=0, sticky=(E, W))
        emailEntry.grid(column=1, row=0, sticky=(E, W), pady=10)
        passwordLabel.grid(column=0, row=1, sticky=(E, W))
        passwordValidationLabel.grid(column=0, row=2, sticky=(E, W))
        passwordEntry.grid(column=1, row=1, sticky=(E, W), pady=10)
        passwordValidationEntry.grid(column=1, row=2, sticky=(E, W), pady=10)
        modifyInfoButton.grid(column=0, columnspan=2, row=3, sticky=(S), pady=10)

        emailEntry.focus()

    def downloadThreadMonitor(self, thread):
        if thread.is_alive():
            self.App.after(100, lambda: self.downloadThreadMonitor(thread))
        else:
            self.downloadProgressBar.stop()
            time.sleep(2)
            self.downloadProgressBar.destroy()
            self.downloadTitleLabel.destroy()
            self.errorMessageLabel.destroy()

    def userOperationsThreadMonitor(self, thread):
        if thread.is_alive():
            self.App.after(
                100, lambda: self.userOperationsThreadMonitor(thread))
        else:
            self.downloadPage()

    def downloadHandler(self, *args):
        self.downloadTitleLabel = ttk.Label(
            self.mainFrame, padding=(0, 0, 15, 0))
        self.downloadProgressBar = ttk.Progressbar(
            self.mainFrame, orient=HORIZONTAL, length=280, mode='indeterminate')
        self.errorMessageLabel = ttk.Label(self.mainFrame, padding=(
            10, 10, 10, 10), text='Please insert a valid YouTube link')

        if self.user != []:
            downloadThread = AsyncDownload(
                self.url, self.formatSelectionVar, self.downloadTitleLabel, self.downloadProgressBar, self.errorMessageLabel, self.user, self.videoHistory)
        else:
            downloadThread = AsyncDownload(
                self.url, self.formatSelectionVar, self.downloadTitleLabel, self.downloadProgressBar, self.errorMessageLabel)

        downloadThread.start()
        self.downloadThreadMonitor(downloadThread)

    def loginHandler(self):
        loginThread = AsyncDatabaseOperations(
            'login', {'email': self.email.get(), 'password': self.password.get(), 'videoHistory': self.videoHistory, 'errorMessageLabel': self.errorMessageLabel}, self.user)

        loginThread.start()
        self.userOperationsThreadMonitor(loginThread)

    def signinHandler(self):
        signinThread = AsyncDatabaseOperations(
            'signin', {'email': self.email.get(), 'password': self.password.get(), 'errorMessageLabel': self.errorMessageLabel, 'videoHistory': self.videoHistory}, self.user)

        signinThread.start()
        self.userOperationsThreadMonitor(signinThread)

    def modifyAccountInfoHandler(self):
        modifyAccountInfoThread = AsyncDatabaseOperations(
            'modifyAccountInfo', {'originalMail': self.user[0][1], 'email': self.email.get(), 'password': self.password.get(), 'videoHistory': self.videoHistory, 'errorMessageLabel': self.errorMessageLabel}, self.user)

        modifyAccountInfoThread.start()
        self.userOperationsThreadMonitor(modifyAccountInfoThread)

    def clearFrame(self):
        for widgets in self.mainFrame.winfo_children():
            widgets.destroy()

    def copyToClipboard(self, text):
        self.App.clipboard_clear()
        self.App.clipboard_append(text)

    def pasteFromClipboard(self, variable):
        variable.set(self.App.clipboard_get())

if __name__ == "__main__":
    App = Tk()
    YoutubeDownloader(App)
    App.mainloop()
