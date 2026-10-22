# S&P DOMEO EVO pour Home Assistant (version de test)

Intégration Home Assistant pour les VMC double flux **S&P DOMEO EVO** (225, 315, 450 ;
FL, DHU, Sérénité), par Modbus RTU via une passerelle TCP ou un adaptateur USB RS485.

> Version de test, en vue d'une intégration dans Home Assistant Core.
> Discussion et retours : https://forum.hacf.fr/t/vmc-s-p-domeo-evo-225-fl-via-modbus-tcp-rtu/69801

## Prérequis

- Home Assistant **2026.10.2** ou plus récent.
- Cavalier **JP1** fermé sur la carte de la VMC.
- Passerelle en **Modbus TCP vers RTU**, **19200 bauds, 8 bits, parité paire, 1 bit de stop**.

## Installation

HACS → ⋮ → Dépôts personnalisés → ce dépôt, catégorie « Intégration » → Télécharger,
puis redémarrer. Ou copier `custom_components/domeo_evo` dans `config/custom_components/`.

Ensuite : Paramètres → Appareils et services → Ajouter une intégration → « S&P DOMEO EVO ».

## Ce qui est écrit dans la VMC

Rien, tant que vous n'actionnez pas une commande. Les registres 40001 à 40003
(adresse, vitesse, parité) ne sont jamais écrits.

Version 0.1.0. La bibliothèque `domeo-evo-modbus` est embarquée dans le dossier.
