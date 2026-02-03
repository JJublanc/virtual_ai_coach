# Plan Marketing V2 - Virtual AI Coach
## Réaliste, 30 min/jour, automatisé au maximum

**Date** : 2026-02-03
**Contexte** : Zéro trafic, comptes froids, 30 min/jour disponibles
**Choix stratégiques** : Marché anglophone, nouveau domaine, Substack comme canal principal

---

## Principes directeurs

1. **Un seul canal, bien exécuté** > 5 canaux médiocres
2. **Contenu recyclé** > Contenu original à chaque fois
3. **Audience owned (newsletter)** > Audience rented (Medium, YouTube)
4. **SEO long terme** ≠ priorité court terme (domain authority = 0)
5. **Build in public** = ta stratégie de différenciation

---

## Phase 0 : Fondations (Semaine 1) - ~5h total

### Actions one-shot (pas récurrentes)

| Action | Temps | Priorité |
|--------|-------|----------|
| Acheter nouveau domaine | 30 min | CRITIQUE |
| Supprimer faux aggregateRating du Schema.org | 10 min | CRITIQUE |
| Installer Google Analytics 4 | 20 min | CRITIQUE |
| Installer Google Search Console | 20 min | CRITIQUE |
| Créer compte Substack | 15 min | CRITIQUE |
| Configurer profil Substack (bio, photo, links) | 30 min | HAUTE |
| Créer compte Buffer/Typefully pour scheduling | 15 min | HAUTE |
| Configurer Make.com/Zapier pour automatisation | 1h | MOYENNE |

### Choix du domaine

**Options recommandées** (à vérifier la disponibilité) :

| Domaine | Pour | Contre |
|---------|------|--------|
| `virtualaicoach.com` | Nom actuel du projet, descriptif | Peut-être pris |
| `workoutgenerator.ai` | Descriptif, mémorisable | Extension .ai plus chère (~$80/an) |
| `fitgen.ai` | Court, moderne | Moins descriptif |
| `aicoach.fit` | Court, extension fitness native | Moins connu que .com |
| `myfitcoach.ai` | Personnel, clair | Peut-être pris |

**Action** : Vérifier sur [Namecheap](https://www.namecheap.com/domains/domain-name-search/) ou [Porkbun](https://porkbun.com)

### Corrections techniques urgentes

**1. Supprimer le faux rating** (`frontend/app/layout.tsx`) :
```typescript
// SUPPRIMER CES LIGNES :
"aggregateRating": {
  "@type": "AggregateRating",
  "ratingValue": "4.8",
  "ratingCount": "150"
}
```

**2. Ajouter Google Analytics 4** (`frontend/app/layout.tsx`) :
```typescript
// Dans le head, ajouter :
<Script
  src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"
  strategy="afterInteractive"
/>
<Script id="google-analytics" strategy="afterInteractive">
  {`
    window.dataLayer = window.dataLayer || [];
    function gtag(){dataLayer.push(arguments);}
    gtag('js', new Date());
    gtag('config', 'G-XXXXXXXXXX');
  `}
</Script>
```

---

## Phase 1 : Lancement Substack (Semaines 2-4) - 30 min/jour

### Stratégie de contenu

**Positionnement Substack** : "Building a fitness app in public - A developer's journey from injury to code"

**Fréquence** : 1 article/semaine (réaliste avec 30 min/jour)

**Format type** :
- 800-1200 mots
- 1 histoire personnelle + 1 leçon pratique
- CTA vers l'app à la fin

### Calendrier de publication (4 premières semaines)

| Semaine | Article | Source | Temps rédaction |
|---------|---------|--------|-----------------|
| 2 | "How I Rebuilt My Body After Years of Pain" | Article 1 (déjà écrit, adapter pour Substack) | 1h (adaptation) |
| 3 | "The Great Escape: How Cycling Became My Shield Against Burnout" | Article 4 (traduire en anglais) | 2h (traduction) |
| 4 | "Generating Videos: Not So Simple!" | Article 3 (traduire + adapter) | 2h |
| 5 | "The Loneliness of Side Project Developers" | Article 2 (traduire + adapter) | 2h |

**Note** : Tes 4 articles sont ton stock initial. 1 mois de contenu déjà prêt.

### Routine quotidienne (30 min)

| Jour | Activité | Temps |
|------|----------|-------|
| Lundi | Rédaction article (1/4 du temps) | 30 min |
| Mardi | Rédaction article (2/4) | 30 min |
| Mercredi | Rédaction article (3/4) | 30 min |
| Jeudi | Finalisation + scheduling | 30 min |
| Vendredi | Cross-posting Reddit + engagement | 30 min |
| Samedi | Repos ou rattrapage | - |
| Dimanche | Review analytics + ajustements | 30 min |

---

## Phase 2 : Distribution Reddit (Semaines 2-8) - intégré aux 30 min

### Subreddits cibles

**Priorité 1 - Ton audience naturelle** :
- r/SideProject (~150k) - partage de projets perso
- r/buildinpublic (~30k) - exactement ton angle
- r/indiehackers (~50k) - solopreneurs tech

**Priorité 2 - Fitness avec angle tech** :
- r/bodyweightfitness (~3M) - uniquement si contenu ultra pertinent
- r/homegym (~800k) - angle "workout at home"
- r/fitness (~11M) - très strict, approche prudente

**Priorité 3 - Développeurs** :
- r/webdev (~2M) - articles techniques
- r/reactjs (~400k) - si contenu Next.js pertinent
- r/Python (~1.5M) - backend stories

### Stratégie Reddit (non-spam)

**Règle d'or** : 90% valeur, 10% promotion

**Semaines 2-4** : Lurk + commentaires utiles (pas de post propre)
- 2-3 commentaires/jour sur des threads pertinents
- Construire du karma et une réputation
- Pas de mention de ton app

**Semaines 5-8** : Posts stratégiques
- 1 post/semaine max sur r/SideProject ou r/buildinpublic
- Format : histoire + leçons, pas pitch produit
- Lien vers Substack, pas vers l'app directement

**Template de post Reddit** :
```
Title: I spent 6 months building a fitness app alone - here's what I learned about [X]

Body:
[Histoire personnelle - 2 paragraphes]
[Leçon concrète - 3 bullet points]
[Question ouverte pour engagement]

---
I'm documenting this journey on my Substack: [lien]
```

---

## Phase 3 : Automatisation (Semaine 5+)

### Stack d'automatisation gratuite/low-cost

| Outil | Usage | Coût |
|-------|-------|------|
| **Buffer** (gratuit) | Scheduling cross-posts | 0€ |
| **Typefully** (gratuit) | Drafts + threads si tu changes d'avis sur X | 0€ |
| **Make.com** (gratuit 1000 ops/mois) | Automatiser republication | 0€ |
| **Zapier** (alternative) | Idem | 0€ (plan gratuit) |
| **IFTTT** (gratuit) | Triggers simples | 0€ |

### Workflow automatisé

```
Substack publish
    │
    ├──> Make.com trigger
    │       │
    │       ├──> Cross-post excerpt sur Dev.to (via API)
    │       ├──> Tweet thread (si tu ouvres X un jour)
    │       └──> Notification Slack/Discord pour toi
    │
    └──> Manuel : Post Reddit adapté (pas automatisable sans ban)
```

### Script de recyclage de contenu

Chaque article Substack génère :
1. **1 post Reddit** (adapté au subreddit)
2. **1 excerpt Dev.to** (version technique)
3. **3-5 quotes** pour micro-contenu futur
4. **1 thread potentiel** (si tu ouvres X/Threads un jour)

---

## Phase 4 : SEO progressif (Mois 2-6)

### Stratégie long terme

**Court terme (0-3 mois)** : Ignorer le SEO Google. Domain authority = 0, pas de backlinks. Investir ici maintenant = ROI nul.

**Moyen terme (3-6 mois)** :
- Chaque article Substack = republié sur blog tyswee.com/blog (canonique Substack)
- Accumulation progressive de contenu indexé
- Backlinks naturels via Reddit/Dev.to

### Keywords à long terme (pour plus tard)

| Keyword | Difficulté | Stratégie |
|---------|-----------|-----------|
| "AI workout generator" | Haute | Article pilier + temps |
| "build in public fitness app" | Basse | Niche, attaquable |
| "solo developer fitness project" | Très basse | Long-tail, facile |
| "home workout video generator" | Moyenne | Article technique |

---

## Métriques à suivre

### Substack (hebdo)

| Métrique | Objectif Mois 1 | Mois 3 | Mois 6 |
|----------|-----------------|--------|--------|
| Subscribers | 50 | 200 | 500 |
| Open rate | >40% | >35% | >30% |
| Article views | 100/article | 300 | 500 |

### Site (mensuel)

| Métrique | Objectif Mois 1 | Mois 3 | Mois 6 |
|----------|-----------------|--------|--------|
| Visites uniques | 100 | 500 | 2000 |
| Workouts générés | 50 | 200 | 1000 |
| Temps sur site | >2 min | >2.5 min | >3 min |

### Reddit (mensuel)

| Métrique | Objectif |
|----------|----------|
| Karma gagné | +100/mois |
| Posts avec >50 upvotes | 1-2/mois |
| Referral traffic | Mesurer via UTM |

---

## Ce qu'on NE fait PAS (pour rester réaliste)

| Action du plan V1 | Pourquoi on abandonne |
|-------------------|----------------------|
| YouTube Shorts quotidiens | Trop chronophage pour 30 min/jour |
| TikTok/Instagram | Hors contrainte (pas de réseaux sociaux mainstream) |
| Email sequence 5 emails | Prématuré sans audience |
| Cold email B2B | Phase 2/3 minimum |
| Product Hunt | Quand tu auras 200+ subscribers Substack |
| Discord community | Quand tu auras 500+ subscribers |
| Paid ads | Jamais avec 0€ budget et pas de PMF validé |
| 1-2 articles/semaine | Irréaliste, 1/semaine max |

---

## Checklist de lancement

### Semaine 1 (fondations)
- [ ] Acheter nouveau domaine
- [ ] Configurer redirection tyswee.com → nouveau domaine
- [ ] Supprimer faux aggregateRating
- [ ] Installer GA4
- [ ] Créer Google Search Console
- [ ] Créer Substack + configurer profil
- [ ] Adapter Article 1 pour Substack

### Semaine 2 (premier publish)
- [ ] Publier Article 1 sur Substack
- [ ] Commenter sur 10 posts Reddit (karma building)
- [ ] Configurer Buffer pour scheduling

### Semaine 3
- [ ] Publier Article 4 (traduit) sur Substack
- [ ] Premier post Reddit sur r/SideProject
- [ ] Review analytics

### Semaine 4
- [ ] Publier Article 3 sur Substack
- [ ] Continuer engagement Reddit
- [ ] Configurer Make.com pour automatisation

---

## Budget temps réel

| Activité | Temps/semaine |
|----------|---------------|
| Rédaction/adaptation article | 2h |
| Reddit engagement | 1h |
| Review analytics | 30 min |
| Admin (scheduling, etc.) | 30 min |
| **TOTAL** | **4h/semaine = 34 min/jour** |

**Verdict** : Le plan tient dans les 30 min/jour avec une marge d'erreur.

---

## Résumé exécutif

**Canal principal** : Substack (newsletter + blog intégré)
**Distribution** : Reddit (r/SideProject, r/buildinpublic, r/indiehackers)
**Fréquence** : 1 article/semaine
**Automatisation** : Make.com pour cross-posting
**SEO** : Reporté à M3+, focus distribution d'abord
**Métriques** : 50 subscribers Substack en M1, 500 en M6

**Prochaine action immédiate** : Acheter le domaine + supprimer le faux rating Schema.org.
