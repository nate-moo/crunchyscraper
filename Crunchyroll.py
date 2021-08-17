###
#
# For use with Firefox download the geckodriver binary and Firefox and uncomment out the following lines:9, 10, 27-29
# and comment out the following lines: 8, 20-25
# 
###

from msedge import selenium_tools
# from selenium import webdriver
# from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import ElementNotInteractableException
from fuzzywuzzy import process
from PyQt5 import QtWidgets
from PyQt5.QtCore import QObject, QThread, pyqtSignal
from mainUI import Ui_MainWindow
import json
import sys
import youtube_dl

opts = selenium_tools.EdgeOptions()
opts.headless = True
opts.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4598.0 Safari/537.36 Edg/94.0.985.0")

opts.use_chromium = True
driver = selenium_tools.Edge(options=opts)

#     opts = Options()
#     opts.headless = True
#     driver = webdriver.Firefox(options=opts)

try:
    class mainWindow(QtWidgets.QMainWindow):
        def __init__(self):
            super(mainWindow, self).__init__()
            self.ui = Ui_MainWindow()
            self.ui.setupUi(self)
            self.ui.pushButton.clicked.connect(self.btnSearch)
            self.ui.pushButton_2.clicked.connect(self.btnAquireSeasons)
            self.ui.pushButton_3.clicked.connect(self.btnAquireEpisodes)
            self.ui.lineEdit.returnPressed.connect(self.btnSearch)
            self.resList = list()
        def btnSearch(self):
            res = search(self.ui.lineEdit.text().replace(" ", "-"))
            self.ui.comboBox.clear()
            self.resList = list()
            for i in res:
                self.resList.append(i[0])
                self.ui.comboBox.addItem(i[0].replace("https://crunchyroll.com/", "").replace("-", " "))
            
            # print("clicked")
        def btnAquireSeasons(self):
            global showlink
            showlink = self.resList[self.ui.comboBox.currentIndex()]
            print(showlink)
            global seasonList
            seasonList = seasons(showlink)
            self.ui.comboBox_2.clear()
            for i in seasonList:
                self.ui.comboBox_2.addItem(i)

        def btnAquireEpisodes(self):
            global sel
            sel = self.ui.comboBox_2.currentIndex()
            self.thread = QThread()
            self.worker = Worker()
            self.worker.moveToThread(self.thread)
            self.thread.started.connect(self.worker.run)
            self.worker.finished.connect(self.thread.quit)
            self.worker.finished.connect(self.worker.deleteLater)
            self.thread.finished.connect(self.thread.deleteLater)
            self.thread.start()
            # self.ui.pushButton.setEnabled(False)


    app = QtWidgets.QApplication([])
    application = mainWindow()
    application.show()

    class Worker(QObject):
        finished = pyqtSignal()
        progress = pyqtSignal(int)

        def run(self):
            driver.get(showlink)
            seasonsVar = driver.find_elements_by_class_name("season")
            global sel
            episodes = seasonsVar[sel].find_elements_by_class_name("portrait-element")
            links = [x.get_attribute("href") for x in episodes]
            links = links[::1]

            with youtube_dl.YoutubeDL(ytdl_opts) as ytdl:
                for link in links:
                    # print("Im download" + link)
                    ytdl.download([link])

    ytdl_opts = {
        #'hls_prefer_native':True,
        'outtmpl':'%USERPROFILE%/Videos/downloaded/%(title)s-%(id)s.%(ext)s',
        'writesubtitles':True,
        #'allsubtitles':True,
        'subtitleslangs':['enUS'],
        'postprocessors':[{
            'key':'FFmpegEmbedSubtitle'
        }],
        'merge_output_format':"mkv"
    }

    def search(searchTerm):
        driver.get("https://www.crunchyroll.com/ajax/?req=RpcApiSearch_GetSearchCandidates")
        secString = driver.find_element_by_tag_name("pre")
        secString = secString.text.replace("/*-secure-", "").replace("*/", "")
        parsedJson = json.loads(secString)["data"]
        print(searchTerm)
        nameList = list()
        for i in parsedJson:
            nameList.append("https://crunchyroll.com" + i["link"])
        fuzzed = process.extract(searchTerm, nameList)
        print(fuzzed)
        return fuzzed


    def seasons(baseURL):
        try:
            driver.get(baseURL)
            seasonsVar = driver.find_elements_by_class_name("season")

            seasonList = list()
            for a in seasonsVar:
                a.click()
                seasonList.append(a.find_element_by_class_name("season-dropdown").text)
        except ElementNotInteractableException as e:
            showName = baseURL.replace("https://crunchyroll.com/", "").replace("-", "")
            seasonList.append(showName)
        return seasonList

    sys.exit(app.exec())

except Exception as e:
    print(e)
    driver.quit()
    exit()

