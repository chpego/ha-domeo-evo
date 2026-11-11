# S&P DOMEO EVO pour Home Assistant

<img src="https://raw.githubusercontent.com/chpego/ha-domeo-evo/main/custom_components/domeo_evo/brand/icon.png" alt="" width="96" align="right">

Lire et piloter une VMC double flux **S&P DOMEO EVO** (225, 315, 450 ; FL, RD, DHU, Sérénité) depuis Home Assistant, par son port Modbus RTU.

- **En local**, par une passerelle RS485 vers Modbus TCP ou un adaptateur USB RS485. Ni cloud, ni compte.
- **Configuration depuis l'interface** : le type de liaison, le modèle et la variante.
- **Sans risque pour la liaison** : l'intégration n'écrit jamais l'adresse, la vitesse ou la parité de la VMC, et n'écrit rien tant que vous n'utilisez pas une commande.

[English version](README.md)

> [!NOTE]
> Cette intégration est en **bêta**. Les registres suivent la table officielle S&P, et les premières vraies VMC sont en test sur le [forum HACF](https://forum.hacf.fr/t/vmc-s-p-domeo-evo-225-fl-via-modbus-tcp-rtu/69801). Voir [Limites connues](#limites-connues).

## Prérequis

- Home Assistant **2026.10.2** ou plus récent.
- Cavalier **JP1** fermé sur la carte de la VMC. JP1 ouvert, la VMC répond aux lectures mais refuse toutes les commandes. Une fois JP1 fermé, la VMC ignore sa propre télécommande. Coupez l'alimentation avant d'ouvrir la VMC.
- Une liaison vers le bornier RS485 de la VMC (A, B, GND) :
  - une **passerelle** (Waveshare RS485 TO ETH, Elfin EW11…) en mode **Modbus TCP vers RTU**, ou
  - un **adaptateur USB RS485** sur la machine Home Assistant.
- Réglages de ligne : **19200 bauds, 8 bits de données, parité paire, 1 bit de stop**. Ce sont les réglages d'usine. 9600 bauds ou 2 bits de stop, parfois conseillés ailleurs, ne fonctionnent pas.

## Installation

[![Ouvrir ce dépôt dans le Marketplace de votre Home Assistant.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=chpego&repository=ha-domeo-evo&category=integration)

Ou à la main : **Marketplace → ⋮ → Dépôts personnalisés**, ajoutez `https://github.com/chpego/ha-domeo-evo` avec le type **Intégration**, puis téléchargez **S&P DOMEO EVO**. Pour recevoir les bêtas, activez l'option **Pré-version** du dépôt.

Sans le Marketplace : copiez `custom_components/domeo_evo` dans votre dossier `config/custom_components/` et redémarrez Home Assistant.

## Configuration

[![Commencer la configuration de S&P DOMEO EVO dans votre Home Assistant.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=domeo_evo)

Ou **Paramètres → Appareils et services → Ajouter une intégration → S&P DOMEO EVO**, puis :

1. Choisissez **Réseau** (passerelle) ou **Port série** (adaptateur USB).
2. Indiquez l'adresse et le port de la passerelle (souvent 502), ou le port série.
3. Laissez l'ID à **1**, sauf si vous l'avez changé.
4. Choisissez le **modèle** inscrit sur la plaque (225, 315 ou 450) et la **variante**. La VMC ne les indique pas, et ils fixent les plages de débit et les réglages hygro.

Si vous avez aussi une configuration YAML `modbus:` pour cette VMC, désactivez-la, ou vérifiez que la passerelle accepte plusieurs clients (Waveshare : **multi-hôte**).

## Entités

| Type | Entités |
| --- | --- |
| Capteurs | Débit, mode de fonctionnement, les cinq températures d'air, batterie de préchauffage, télécommande, entrée 0-10 V ; humidité intégrée (DHU, Sérénité) ; un capteur par sonde AIRSENS (humidité, CO₂ ou COV), détectée automatiquement |
| Capteurs binaires | Remplacement du filtre, dégivrage, défauts moteurs, défauts des sondes de température, contact CLP, **Pilotage Modbus (JP1)** |
| Interrupteurs | Mode vacances, by-pass manuel, by-pass automatique, dégivrage autorisé |
| Boutons | Démarrer le boost, arrêter le boost, réinitialiser l'alarme filtre |
| Listes | Mode automatique (proportionnel ou agile), type de contact CLP |
| Nombres | Débits bas, haut et freecooling (bornés selon le modèle), seuils de by-pass, durée du by-pass manuel, intervalle du filtre, correction et décalage du débit ; régulation hygro et qualité d'air (DHU, Sérénité) |

Certaines entités de diagnostic et de configuration sont désactivées par défaut. Activez-les depuis la page de l'appareil.

Un bouton affiche **Inconnu** tant qu'il n'a jamais été pressé. C'est le fonctionnement normal de Home Assistant, pas une erreur.

## Ce que l'intégration écrit

Rien, tant que vous n'utilisez pas une commande. Elle n'écrit jamais les registres 40001 à 40003 (adresse, vitesse et parité de la VMC) : une mauvaise valeur y coupe la liaison au prochain redémarrage. Elle ne propose pas la réinitialisation des ID AIRSENS (coil 9), qui oublie les sondes appairées. Elle ne lit que les adresses documentées dans la table S&P.

## Limites connues

En cours de confirmation sur de vraies VMC :

- **Mode vacances.** La table S&P indique pour le coil 4 « 0 = On », et l'intégration la suit. Une première vraie VMC suggère l'inverse. Si l'interrupteur affiche le contraire de ce que fait votre VMC, signalez-le dans une issue.
- **Arrêt du boost.** La table dit qu'écrire 0 arrête le boost ; le support S&P a répondu à un utilisateur que c'était impossible (il s'arrête seul). L'intégration envoie ce 0 en écriture multiple (FC16).
- **Reset du filtre.** L'intégration écrit le coil 8, comme l'indique la table.

La VMC n'a pas de numéro de série : Home Assistant ne peut pas la reconnaître après un changement de liaison. Utilisez **Reconfigurer** sur l'intégration plutôt que de l'ajouter une seconde fois.

## Dépannage

| Symptôme | Cause et solution |
| --- | --- |
| Une réparation indique *le cavalier JP1 est ouvert*, ou les commandes échouent avec *exception 0x01* | JP1 est ouvert. Coupez le courant, fermez JP1, rallumez. L'entité **Pilotage Modbus (JP1)** passe à « activé ». |
| La configuration indique *la VMC ne répond pas* | Mauvais réglages de ligne ou câblage. Vérifiez 19200 bauds, 8E1, A/B non inversés, et la passerelle en Modbus TCP vers RTU. |
| La VMC ne répond plus après une coupure de courant | Sa parité a peut-être été changée par une écriture YAML erronée dans le registre 40003 (adresse 2). Essayez la parité impaire sur la passerelle, puis réécrivez `2` dans ce registre. |
| Humidité bloquée à 54 % | Aucun capteur d'humidité n'est monté (VMC FL et RD). C'est ce que renvoie la VMC. |
| Température avant échangeur inconnue | Aucune sonde n'est montée à cet endroit ; la VMC la signale en défaut. |

Pour signaler un bug, téléchargez les diagnostics (**⋮ → Télécharger les diagnostics** sur la carte de l'intégration) et joignez le fichier à une [issue](https://github.com/chpego/ha-domeo-evo/issues). L'adresse de la passerelle y est masquée.

## Avertissement et licence

Projet indépendant, sans lien avec S&P (Soler & Palau) ni Unelvent. À utiliser sous votre responsabilité : les commandes modifient le fonctionnement de votre ventilation.

[MIT](LICENSE)
