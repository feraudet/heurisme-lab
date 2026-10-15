# Redémarrer un nœud de la base de données de production

## 1. Avant de commencer

Cette procédure s'applique au cluster PostgreSQL de production, composé d'un nœud primaire et de deux réplicas. Elle ne s'applique pas à l'environnement de préproduction, qui n'a qu'un seul nœud.

Vérifie d'abord qu'aucune sauvegarde n'est en cours. Une sauvegarde interrompue doit être relancée entièrement, ce qui prend environ quatre heures. Les sauvegardes complètes démarrent chaque nuit à deux heures et se terminent en général avant six heures.

Vérifie ensuite que les deux réplicas sont à jour. Le retard de réplication affiché sur le tableau de bord doit être inférieur à dix secondes. S'il dépasse une minute, ne redémarre rien : la cause du retard doit être comprise d'abord.

Préviens l'équipe sur le canal d'incident avant toute intervention, en indiquant le nœud concerné et l'heure prévue du redémarrage.

## 2. Redémarrer un réplica

Un réplica peut être redémarré à tout moment, à condition que l'autre réplica soit en bonne santé. Retire d'abord le réplica de la répartition de charge des lectures, attends que les connexions en cours se terminent, puis redémarre le service.

Après le redémarrage, le réplica rattrape son retard tout seul. Remets-le dans la répartition de charge seulement quand son retard est revenu sous dix secondes.

## 3. Redémarrer le primaire

Le primaire ne se redémarre jamais directement. Il faut d'abord basculer : promouvoir un réplica à jour en nouveau primaire, vérifier que les applications écrivent bien sur lui, puis redémarrer l'ancien primaire, qui repart en tant que réplica.

Pendant la bascule, les écritures sont refusées pendant quelques secondes. Les applications doivent réessayer automatiquement ; si une application renvoie des erreurs plus de deux minutes après la bascule, préviens son équipe.

## 4. En cas d'échec

Si le service ne redémarre pas, consulte les journaux du nœud avant toute nouvelle tentative. Les erreurs les plus fréquentes sont un disque plein et un fichier de configuration modifié à la main. Ne supprime jamais de fichiers dans le répertoire des données pour libérer de la place : escalade vers le niveau 2.
