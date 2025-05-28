[![DOI](https://zenodo.org/badge/102614780.svg)](https://zenodo.org/badge/latestdoi/102614780)

# FLIR-A320-control: Contrôle et traitement de données RAW de caméra FLIR A320

Ce projet est un **fork** du dépôt original de [Jonathan D. Müller](https://zenodo.org/record/4088156), initialement conçu pour contrôler une caméra infrarouge FLIR A320 via Telnet.  
**Fork réalisé et adapté par : Alexy Pefaure**  
**Objectif du fork :** ajouter des fonctionnalités de **traitement de données RAW** capturées par la caméra, pour permettre des analyses plus avancées des images infrarouges.

---

## Fonctionnalités principales

- Contrôle de la caméra FLIR A320 via Telnet.
- Réglage des paramètres de la caméra.
- Capture d'images à intervalles réguliers.
- **(Ajouté)** Extraction et traitement des données RAW issues de la caméra.

---

## Prérequis
Installez les dépendances nécessaires via apt :

```bash
apt install exiftool
```

Installez les dépendances nécessaires via pip :

```bash
pip3 install -r requirements.txt
```
Conversion du fichier Qt Designer .ui en .py

Si vous modifiez l’interface graphique, convertissez le fichier .ui comme suit :
```bash
pyuic5 -o Interface.py Interface.ui
```
Comment citer ce travail

Jonathan D. Muller. (2020, October 14). FLIR-A320-control: Control FLIR A320 infrared camera. doi: 10.5281/zenodo.4088156 (URL: https://zenodo.org/record/4088156)
Fork adapté par Alexy Pefaure pour l'analyse des données RAW infrarouges.
Licence
Logiciel

Ce logiciel est distribué sous licence GPL version 3.
Logos et icônes

Tous les logos et icônes sont la propriété de FLIR.
