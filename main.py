#-------------------------------------------------------------------------------
# Name:        FLIR A320 control software
# Purpose:	   This software controls the FLIR A320
#
# Author:      Jonathan D. Müller
#
# Created:     03/09/2017
# Copyright:   (c) Jonathan D. Müller 2017
# Licence:     GPL
#Forké par : Alexy Pefaure 
#Date : 28/05/2025
#Modifications : changement d'interface, traitement de données raw]
#-------------------------------------------------------------------------------

# System stuff
import datetime, ctypes
from time import strftime # For logging
from os.path import expanduser # for user directory
import os.path

# Import Qt5
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

# Import the user interface
from Interface import *
import functions.flir
flir = functions.flir.FLIR



import os
import cv2
import numpy as np
import matplotlib.pyplot as plt
import ffmpeg
import shutil
import matplotlib.patches as patches

# Logging
import logging
import sys
log = logging.getLogger('root')
log.setLevel(logging.DEBUG)
stream = logging.StreamHandler(sys.stdout)
stream.setLevel(logging.DEBUG)
formatter = logging.Formatter('[%(asctime)s] %(levelname)8s %(module)15s: %(message)s')
stream.setFormatter(formatter)
log.addHandler(stream)

class Main(QMainWindow, Ui_Dialog):
    def __init__(self, parent=None):
        QMainWindow.__init__(self)
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        log.info("Starting FLIR program")
        self.cam = None
        self.currentImg = None
        self.logFolder = ''
        self.zone = (slice(0, 320), slice(0, 240))
		
        # initialise the data list: 1x Date, 2x Arduino, 4x 6262
        #self.data = [float('nan')]*7
        # These threads run in the background
        self.initUI()
        
        self.flir_running = False
        #self.logging_running = False
        self.video_logging_running = False

        # set up timer
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.timed_tasks)


    def initUI(self):
        # Check for COM ports and add them
        #
        self.ui.connect.clicked.connect(self.connectFLIR) # & flirIP
        #self.ui.autofocusFull.clicked.connect(self.autofocusFull) #if you want to add the focus you have to put on the interface the button and uncomment this
        #self.ui.autofocusQuick.clicked.connect(self.autofocusQuick)
        self.ui.shootNow.clicked.connect(self.start_photo_process)
        self.ui.setAtmT.clicked.connect(self.setAtmT) #atmT
        self.ui.setAmbT.clicked.connect(self.setAmbT) #ambT
        self.ui.setDist.clicked.connect(self.setDist) #dist
        self.ui.setRH.clicked.connect(self.setRH)     #rh
        self.ui.setEmissivity.clicked.connect(self.setEmissivity) #emissivity
        self.ui.IntervalSet.clicked.connect(self.setInterval) #IntervalTime
        #self.ui.chooseFolderButton.clicked.connect(self.folderChooser)
        # put in some new default
        #self.ui.IntervalTime.setText("240")
        self.ui.setZone.clicked.connect(self.setZone)
        self.ui.Startvideo.clicked.connect(self.start_video_process)

    def timed_tasks(self):
        fichier_ordre = "fichiers_ordre.txt"
        self.shootNow()
        fichier = self.currentImg
        nom_fichier = os.path.basename(fichier)
        with open(fichier_ordre, "a", encoding="utf-8") as f_out:
            f_out.write(nom_fichier + "\n")

        


    def connectFLIR(self):
        if(self.flir_running == True):
            log.info("Disconnecting FLIR")
            self.cam.close()
            del self.cam
            self.ui.connect.setText("Connect")
            self.flir_running = False
        else:
            log.info("Connecting FLIR " + self.ui.flirIP.text())
            self.cam = flir(self.ui.flirIP.text())
            try:
                self.cam.connect()
            except:
                pass
            else:
                log.info("Setting camera date & time")
                self.cam.setDateTime()
                self.ui.connect.setText("Disconnect")
                self.flir_running = True
                log.info("Camera ready")


    """ def autofocusFull(self):
        log.info("Full autofocus")
        try:
            self.cam.slowFocus()
        except:
            QMessageBox.warning(None,"Connect","Please connect the camera.")  """

    """  def autofocusQuick(self):
        log.info("Quick autofocus")
        try:
            self.cam.quickFocus()
        except:
            QMessageBox.warning(None,"Connect","Please connect the camera.") """

    def shootNow(self):
        log.info("shoot to " + self.logFolder)
        if(self.logFolder == ''):
            if not os.path.exists(self.logFolder + 'jpg'):
                os.makedirs(self.logFolder + 'jpg')
            if not os.path.exists(self.logFolder + 'tif'):
                os.makedirs(self.logFolder + 'tif')
            if not os.path.exists(self.logFolder + 'rawdata'):
                os.makedirs(self.logFolder + 'rawdata')
            self.folderjpg = self.logFolder + 'jpg/'
            self.foldertif = self.logFolder + 'tif/'
            self.folderrawdata = self.logFolder + 'rawdata/'
        else:
            if not os.path.exists(self.logFolder + '/jpg'):
                os.makedirs(self.logFolder + '/jpg')
            if not os.path.exists(self.logFolder + '/tif'):
                os.makedirs(self.logFolder + '/tif')
            if not os.path.exists(self.logFolder + '/rawdata'):
                os.makedirs(self.logFolder + '/rawdata')
            self.folderjpg = self.logFolder + "/jpg/"
            self.foldertif = self.logFolder + '/tif/'
            self.folderrawdata = self.logFolder + '/rawdata/'
        
        try:
            self.currentImg = self.cam.shootJPG(self.folderjpg)
            base = os.path.splitext(os.path.basename(self.currentImg))[0]
            self.currenttif = base + ".tif"
            self.currenttif_path = os.path.join(self.logFolder, "tif", self.currenttif)
            cmd = f'exiftool -b -RawThermalImage "{self.currentImg}" > "{self.currenttif_path}"'
            os.system(cmd)
            thermal_array = cv2.imread(self.currenttif_path, cv2.IMREAD_UNCHANGED)
            csv_path = os.path.join(self.folderrawdata, 'raw_data-' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S') + '.csv')
            np.savetxt(csv_path, thermal_array, delimiter=",", fmt="%d") 
        except:
            QMessageBox.warning(None,"Connect","Please connect the camera.")
        else:
            # Now show the resulting image
            log.info("Created file " + self.currentImg)
            image = QtGui.QImage(self.currentImg)
            image = image.scaled(640,480, aspectRatioMode=QtCore.Qt.KeepAspectRatio, transformMode=QtCore.Qt.SmoothTransformation) # To scale image for example and keep its Aspect Ration    
            self.ui.currentImg.setPixmap(QtGui.QPixmap.fromImage(image))
		
    def setAtmT(self):
        log.info("set atmospheric T " + self.ui.atmT.text())
        try:
            self.cam.setAtmT(float(self.ui.atmT.text()))
        except:
            QMessageBox.warning(None,"Connect","Please connect the camera.")

    def setAmbT(self):
        log.info("set ambient T " + self.ui.ambT.text())
        try:
            self.cam.setAmbT(float(self.ui.ambT.text()))
        except:
            QMessageBox.warning(None,"Connect","Please connect the camera.")

    def setDist(self):
        log.info("set distance " + self.ui.dist.text())
        try:
            self.cam.setDist(float(self.ui.dist.text()))
        except:
            QMessageBox.warning(None,"Connect","Please connect the camera.")

    def setRH(self):
        log.info("set relative humidity " + self.ui.rh.text())
        self.cam.setRH(float(self.ui.rh.text())/100)
        try:
            self.cam.setRH(float(self.ui.rh.text())/100)
        except:
            QMessageBox.warning(None,"Connect","Please connect the camera.")

    def setEmissivity(self):
        log.info("set emissivity " + self.ui.emissivity.text())
        try:
            self.cam.setEmiss(float(self.ui.emissivity.text()))
        except:
            QMessageBox.warning(None,"Connect","Please connect the camera.")
		
    def setInterval(self):
        log.info("set interval " + self.ui.IntervalTime.text())
        try:
            pass
        except:
            QMessageBox.warning(None,"Connect","Please connect the camera.")
		
    def folderChooser(self):
        fname = QFileDialog.getExistingDirectory(self, "Select Directory",
                        expanduser("~\Documents"))
        if(fname == ""):
            log.debug("No folder selected")
            QMessageBox.warning(None,"No folder selected","Please select a log folder.")
        else:
            log.info(fname)
            self.logFolder = fname
            self.ui.logfolder.setText(fname)

    """ def logStart(self):
        if(self.logging_running == True):
            log.info("Stop logging")
            self.ui.LogStart.setText("Start logging")
            self.timer.stop()
            self.logging_running = False
        else:
            # Check if devices are connected
            if(self.flir_running == True):
                # Run every X seconds
                #self.autofocusFull() # first focus
                self.ui.LogStart.setText("Stop logging")
                self.timer.start(int(self.ui.IntervalTime.text())*1000)
                self.logging_running = True
            else:
                QMessageBox.warning(None,"Connect","Please connect the camera.") """
			
    def closeEvent(self, event): # This is when the window is clicked to close
        log.info("Shutting down application")
        try:
            self.cam.close()
        except:
            pass
        log.info("Shutdown completed")
        log.info('------------------')
        event.accept()



    def setZone(self):
        log.info("set zone " + self.ui.setZone.text())
        self.X_debut = int(self.ui.X_debut.text())
        self.X_fin = int(self.ui.X_fin.text())
        self.Y_debut = int(self.ui.Y_debut.text())
        self.Y_fin = int(self.ui.Y_fin.text())
        try:
            self.zoneX = slice(self.X_debut, self.X_fin)
            self.zoneY = slice(self.Y_debut, self.Y_fin)
        except:
            QMessageBox.warning(None,"Zone","Zone impossible")





    def analyser_serie_thermique(self):
        """
        Analyse une série d'images thermiques et affiche la moyenne de température sur une zone définie,
        ainsi que la dernière image en fausses couleurs.
        """
        self.setZone()

        tif_dir = self.foldertif
        fichier_ordre = "fichiers_ordre.txt"

        if not os.path.exists(tif_dir):
            print(f"Dossier .tif non trouvé : {tif_dir}")
            return

        if not os.path.isfile(fichier_ordre):
            print(f"Fichier d'ordre non trouvé : {fichier_ordre}")
            return

        # === Chargement de la liste des fichiers ===
        with open(fichier_ordre, 'r', encoding='utf-8') as f:
            filenames = [line.strip().replace('.jpg', '.tif') for line in f if line.strip()]

        mean_values = []
        timestamps = []
        std_values = []
        last_image = None
        reference_time = None

        for i, filename in enumerate(filenames):
            path = os.path.join(tif_dir, filename)

            # Extraction stricte du timestamp
            base_name = os.path.splitext(filename)[0]
            timestamp_str = base_name[len("file-"):]  # enlève "file-" → reste "20250523-142859"
            file_time = datetime.datetime.strptime(timestamp_str, "%Y%m%d-%H%M%S")
            if reference_time is None:
                reference_time = file_time

            time_seconds = (file_time - reference_time).total_seconds()

            img = cv2.imread(path, cv2.IMREAD_UNCHANGED)

            if img is None:
                print(f"Lecture échouée : {filename}, ignoré.")
                continue

            zone_data = img[self.zoneX, self.zoneY]
            mean_temp = float(np.mean(zone_data))
            std_temp = float(np.std(zone_data))

            mean_values.append(mean_temp)
            timestamps.append(time_seconds)
            std_values.append(std_temp)
            print(mean_values)
            print(std_temp)

            print(f"{filename} ➜ Moyenne : {mean_temp:.2f}")

            last_image = img  # stocker la dernière image valide

        # === Affichage graphique + image ===
        if mean_values:
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

            # Graphe
            #ax1.plot(timestamps, mean_values, marker='o', linestyle='-', color='green')
            ax1.errorbar(timestamps, mean_values, std_values, marker='o', linestyle='-', color='green')
            ax1.set_title("Évolution des données raw moyenne (zone définie)")
            ax1.set_xlabel("Temps (s)")
            ax1.set_ylabel("Données brute moyennées (RAW)")
            ax1.grid(True)

            # Dernière image thermique
            if last_image is not None:
                im = ax2.imshow(last_image, cmap="rainbow")
                ax2.set_title("Dernière image thermique")
                plt.colorbar(im, ax=ax2, label="Valeur brute")
            
            rect = patches.Rectangle((self.X_debut, self.Y_debut),self.X_fin - self.X_debut, self.Y_fin - self.Y_debut, linewidth=1, edgecolor='r', facecolor='none')
            ax2.add_patch(rect)
            plt.tight_layout()
            plt.show()
        else:
            print("Aucune donnée à afficher.")
        
        csv_path = os.path.join(self.logFolder, 'values-' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S') + '.csv')
        data = np.column_stack((timestamps, mean_values, std_values))  # Combine les listes
        np.savetxt(csv_path, data, delimiter=",", header="Temps(s),Moyenne,Écart-type", comments='', fmt="%.3f")

    def analyser_image_simple(self):
        """
        Analyse une seule image thermique et affiche la moyenne de température dans la zone définie.
        """

        self.setZone()

        chemin_image = self.currenttif_path

        if not os.path.isfile(chemin_image):
            print(f"Fichier introuvable : {chemin_image}")
            return

        img = cv2.imread(chemin_image, cv2.IMREAD_UNCHANGED)

        if img is None:
            print(f"Échec de lecture de l’image : {chemin_image}")
            return

        zone_data = img[self.zoneX, self.zoneY]
        mean_temp = float(np.mean(zone_data))
        std_temp = float(np.std(zone_data))

        print(f"Image : {chemin_image}")
        print(f"Moyenne température dans la zone : {mean_temp:.2f}")
        print(f"Écart-type dans la zone : {std_temp:.2f}")

        fig, ax = plt.subplots(figsize=(8, 6))

        im = ax.imshow(img, cmap="rainbow")
        ax.set_title("Dernière image thermique")
        plt.colorbar(im, ax=ax, label="Valeur brute")

        rect = patches.Rectangle(
            (self.X_debut, self.Y_debut),
            self.X_fin - self.X_debut,
            self.Y_fin - self.Y_debut,
            linewidth=2, edgecolor='r', facecolor='none'
        )
        ax.add_patch(rect)

        plt.tight_layout()
        plt.show()

    
    def generer_video_depuis_liste(self):
        """
        Génère une vidéo à partir d'une liste d'images en utilisant ffmpeg,
        en respectant l’ordre du fichier fourni.
        """
        sortie_video = os.path.join(self.logFolder, 'video-' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S') + '.mp4')
        dossier_images = self.folderjpg
        fichier_ordre = "fichiers_ordre.txt"
        supprimer_temporaire = True
        framerate = 1  # 1 image par seconde
        dossier_temporaire = os.path.join(self.logFolder, "temp_images_ffmpeg")

        if not os.path.isfile(fichier_ordre):
            print(f"Fichier d'ordre non trouvé : {fichier_ordre}")
            return

        with open(fichier_ordre, "r", encoding="utf-8") as f:
            fichiers = [ligne.strip() for ligne in f if ligne.strip()]

        if not fichiers:
            print("Aucune image trouvée dans le fichier d’ordre.")
            return

        # Créer un dossier temporaire avec des noms séquentiels
        if os.path.exists(dossier_temporaire):
            shutil.rmtree(dossier_temporaire)
        os.makedirs(dossier_temporaire)

        for i, nom in enumerate(fichiers):
            source = os.path.join(dossier_images, nom)
            if not os.path.isfile(source):
                print(f"[!] Image manquante : {source}")
                continue
            destination = os.path.join(dossier_temporaire, f"frame_{i:04d}.jpg")
            shutil.copy2(source, destination)

        try:
            # Générer la vidéo à partir des images renommées dans l'ordre
            ffmpeg.input(
                os.path.join(dossier_temporaire, 'frame_%04d.jpg'),
                framerate=framerate
            ).output(
                sortie_video,
                vcodec='libx264',
                pix_fmt='yuv420p'
            ).run()
            print(f" Vidéo générée avec succès : {sortie_video}")
        except ffmpeg.Error as e:
            print(" Erreur lors de l'exécution de ffmpeg :", e)
        finally:
            if supprimer_temporaire:
                shutil.rmtree(dossier_temporaire)



    def start_video_process(self):
        if self.video_logging_running:
            # Arrêter le processus
            log.info("Arrêt du processus vidéo")
            self.ui.Startvideo.setText("Démarrer la vidéo")
            self.timer.stop()
            self.video_logging_running = False

            # À la fin, on génère la vidéo et on analyse
            self.generer_video_depuis_liste()
            self.analyser_serie_thermique()

        else:
            # Vérifier que la caméra est connectée
            if self.flir_running:
                log.info("Démarrage du processus vidéo")
                self.ui.Startvideo.setText("Arrêter la vidéo")
                self.video_logging_running = True
                self.folderChooser()
                self.logFolder = os.path.join(self.logFolder, 'video-' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S') + '/')

                with open("fichiers_ordre.txt", "w", encoding="utf-8") as f:
                    pass

                # Lancer le timer qui appelle `timed_tasks` toutes les X secondes
                self.timer.start(int(self.ui.IntervalTime.text()) * 1000)
            else:
                QMessageBox.warning(None, "Connect", "Veuillez connecter la caméra.")


    def start_photo_process(self):
        try:
            self.folderChooser()
            self.logFolder = os.path.join(self.logFolder, 'photo-' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S') + '/')
            self.shootNow()
            self.analyser_image_simple()
        except:
            QMessageBox.warning(None, "Connect", "Veuillez connecter la caméra.")


# Show the image
if __name__ == "__main__":
    # This tells Windows to use my icon
    myappid = 'mycompany.myproduct.subproduct.version' # arbitrary string
   #  ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
	
    app = QApplication(sys.argv)
    myapp = Main()
    myapp.show()
	
    sys.exit(app.exec_())
