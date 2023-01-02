<!-- Generated Document: Do not edit -->

# Card

Card related commands.

## Commands

### card

*[Detail Command](/commands/general-usage/#detail-commands)*

!!! note "Tab Names"
    untrained, trained

!!! question "Description"
    Card details.

### cards

*[List Command](/commands/general-usage/#list-commands)*

!!! question "Description"
    Card list.

## Attributes

### name

!!! abstract "Aliases"
    title

!!! info "Type"
    [Sortable](/commands/general-usage/#sortable)

!!! question "Description"
    Card name.

??? example "Examples"
    `sort=name`  
    `sort<name`

### character

!!! abstract "Aliases"
    char, chara

!!! info "Type"
    [Sortable](/commands/general-usage/#sortable), [Equality](/commands/general-usage/#equality), [Tag](/commands/general-usage/#tag), [Keyword](/commands/general-usage/#keyword)

!!! question "Description"
    Character name.

??? note "Tags"
     - rinku  
     - maho  
     - muni  
     - rei  
     - kyoko  
     - shinobu  
     - yuka  
     - esora  
     - saki  
     - ibuki  
     - towa  
     - noa  
     - rika  
     - marika  
     - saori  
     - dalia  
     - tsubaki  
     - nagisa  
     - hiiro  
     - aoi  
     - miyu  
     - haruna  
     - kurumi  
     - miiko  
     - airi  
     - mana  
     - shano  
     - toka  
     - michiru  
     - lumina  
     - kokoa  
     - hayate  
     - neo  
     - sophia  
     - elsie  
     - weronika

??? example "Examples"
    `sort=character`  
    `sort<character`  
    `character=airi`  
    `character=muni,tsubaki,neo`  
    `character!=muni,tsubaki,neo`  
    `$muni $tsubaki $neo`  
    `$!airi $!shano`  
    `muni tsubaki neo`

### unit

!!! info "Type"
    [Sortable](/commands/general-usage/#sortable), [Equality](/commands/general-usage/#equality), [Tag](/commands/general-usage/#tag)

!!! question "Description"
    Card character unit.

??? note "Tags"
     - happy_around!, happyaround, happy_around, hapiara, happy, ha  
     - peaky_p-key, peakyp-key, peakypkey, peaky, p-key, pkey, pkpk, pk  
     - photon_maiden, photonmaiden, photome, photon, pm  
     - merm4id, mermaid, mmd, m4  
     - 燐舞曲, rondo  
     - lyrical_lily, lyricallily, riririri, lililili, lily, lili, riri, ll  
     - call_of_artemis, callofartemis, coa, c.o.a.  
     - unichørd, unichord, uc, 1c, uni  
     - abyssmare, am, abyss  
     - スペシャル, special  
     - その他, other

??? example "Examples"
    `sort=unit`  
    `sort<unit`  
    `unit=unichørd`  
    `unit=燐舞曲,unichørd,lyrical_lily`  
    `unit!=燐舞曲,unichørd,lyrical_lily`  
    `$燐舞曲 $unichørd $lyrical_lily`  
    `$!unichørd $!call_of_artemis`

### attribute

!!! info "Type"
    [Sortable](/commands/general-usage/#sortable), [Equality](/commands/general-usage/#equality), [Tag](/commands/general-usage/#tag)

!!! question "Description"
    Card attribute.

??? note "Tags"
     - street, purple  
     - party, yellow, orange  
     - cute, pink, red  
     - cool, blue  
     - elegant, green

??? example "Examples"
    `sort=attribute`  
    `sort<attribute`  
    `attribute=elegant`  
    `attribute=elegant,party,cool`  
    `attribute!=elegant,party,cool`  
    `$elegant $party $cool`  
    `$!elegant $!party`

### id

!!! info "Type"
    [Sortable](/commands/general-usage/#sortable), [Display](/commands/general-usage/#display), [Comparable](/commands/general-usage/#comparable)

!!! question "Description"
    Card Id.

??? example "Examples"
    `sort=id`  
    `sort<id`  
    `disp=id`  
    `id=[value]`  
    `id!=[value]`  
    `id>[value]`

### power

!!! abstract "Aliases"
    pow, bp

!!! info "Type"
    [Sortable](/commands/general-usage/#sortable), [Display (Default)](/commands/general-usage/#display), [Comparable](/commands/general-usage/#comparable)

!!! question "Description"
    Total power at max level.

??? example "Examples"
    `sort=power`  
    `sort<power`  
    `disp=power`  
    `power=27649`  
    `power!=27649`  
    `power>27649`

### heart

!!! abstract "Aliases"
    hrt

!!! info "Type"
    [Special Flag](/commands/general-usage/#flag), [Sortable](/commands/general-usage/#sortable), [Display](/commands/general-usage/#display), [Comparable](/commands/general-usage/#comparable)

!!! question "Description"
    Heart stat at max level.

!!! note "Tags"
    heart, hrt

??? example "Examples"
    `$heart`  
    `sort=heart`  
    `sort<heart`  
    `disp=heart`  
    `heart=9082`  
    `heart!=9082`  
    `heart>9082`

### technique

!!! abstract "Aliases"
    tech, technical

!!! info "Type"
    [Special Flag](/commands/general-usage/#flag), [Sortable](/commands/general-usage/#sortable), [Display](/commands/general-usage/#display), [Comparable](/commands/general-usage/#comparable)

!!! question "Description"
    Technique stat at max level.

!!! note "Tags"
    technique, tech, technical

??? example "Examples"
    `$technique`  
    `sort=technique`  
    `sort<technique`  
    `disp=technique`  
    `technique=9219`  
    `technique!=9219`  
    `technique>9219`

### physical

!!! abstract "Aliases"
    phys, physic, physics

!!! info "Type"
    [Special Flag](/commands/general-usage/#flag), [Sortable](/commands/general-usage/#sortable), [Display](/commands/general-usage/#display), [Comparable](/commands/general-usage/#comparable)

!!! question "Description"
    Physical stat at max level.

!!! note "Tags"
    physical, phys, physic, physics

??? example "Examples"
    `$physical`  
    `sort=physical`  
    `sort<physical`  
    `disp=physical`  
    `physical=9348`  
    `physical!=9348`  
    `physical>9348`

### date

!!! abstract "Aliases"
    release, recent

!!! info "Type"
    [Sortable (Default)](/commands/general-usage/#sortable), [Display](/commands/general-usage/#display), [Comparable](/commands/general-usage/#comparable)

!!! question "Description"
    Release date.

??? example "Examples"
    `sort=date`  
    `sort<date`  
    `disp=date`  
    `date=2020/12/31`  
    `date!=2020/12/31`  
    `date>2020/12/31`

### rarity

!!! abstract "Aliases"
    stars

!!! info "Type"
    [Sortable](/commands/general-usage/#sortable), [Keyword](/commands/general-usage/#keyword)

!!! question "Description"
    Star rarity.

??? note "Tags"
     - 4\*, 4\\\*  
     - 3\*, 3\\\*  
     - 2\*, 2\\\*  
     - 1\*, 1\\\*

??? example "Examples"
    `sort=rarity`  
    `sort<rarity`  
    `2* 1* 4*`

### skill

!!! abstract "Aliases"
    score_up, score

!!! info "Type"
    [Sortable](/commands/general-usage/#sortable), [Display](/commands/general-usage/#display), [Comparable](/commands/general-usage/#comparable)

!!! question "Description"
    Card skill.

??? example "Examples"
    `sort=skill`  
    `sort<skill`  
    `disp=skill`  
    `skill=50`  
    `skill!=50`  
    `skill>50`

### groovy_score

!!! abstract "Aliases"
    groovyscore, groovy, fever_score, feverscore, fever, groovy_score_up, groovyscoreup, fever_score_up, feverscoreup, feverup, groovyup, fever_up, groovy_up, feverboost, fever_boost, groovyboost, groovy_boost, gtscore, gtscoreup, gt_score, gt_score_up, gtup, gt_up

!!! info "Type"
    [Flag](/commands/general-usage/#flag), [Sortable](/commands/general-usage/#sortable), [Display](/commands/general-usage/#display), [Comparable](/commands/general-usage/#comparable)

!!! note "Tags"
    groovy_score, groovyscore, groovy, fever_score, feverscore, fever, groovy_score_up, groovyscoreup, fever_score_up, feverscoreup, feverup, groovyup, fever_up, groovy_up, feverboost, fever_boost, groovyboost, groovy_boost, gtscore, gtscoreup, gt_score, gt_score_up, gtup, gt_up

??? example "Examples"
    `$groovy_score`  
    `$!groovy_score`  
    `sort=groovy_score`  
    `sort<groovy_score`  
    `disp=groovy_score`  
    `groovy_score=10`  
    `groovy_score!=10`  
    `groovy_score>10`

### groovy_support

!!! abstract "Aliases"
    groovysupport, fever_support, feversupport, gtsupport, gt_support

!!! info "Type"
    [Flag](/commands/general-usage/#flag), [Sortable](/commands/general-usage/#sortable), [Display](/commands/general-usage/#display), [Comparable](/commands/general-usage/#comparable)

!!! note "Tags"
    groovy_support, groovysupport, fever_support, feversupport, gtsupport, gt_support

??? example "Examples"
    `$groovy_support`  
    `$!groovy_support`  
    `sort=groovy_support`  
    `sort<groovy_support`  
    `disp=groovy_support`  
    `groovy_support=10`  
    `groovy_support!=10`  
    `groovy_support>10`

### solo_groovy

!!! abstract "Aliases"
    solo_fever, solo_gt, sologroovy, solofever, sologt

!!! info "Type"
    [Flag](/commands/general-usage/#flag)

!!! note "Tags"
    solo_groovy, solo_fever, solo_gt, sologroovy, solofever, sologt

??? example "Examples"
    `$solo_groovy`  
    `$!solo_groovy`

### constant_score

!!! abstract "Aliases"
    constantscore, constant_score_up, constantscoreup, passive_score, passivescore, passive_score_up

!!! info "Type"
    [Flag](/commands/general-usage/#flag), [Sortable](/commands/general-usage/#sortable), [Display](/commands/general-usage/#display), [Comparable](/commands/general-usage/#comparable)

!!! note "Tags"
    constant_score, constantscore, constant_score_up, constantscoreup, passive_score, passivescore, passive_score_up

??? example "Examples"
    `$constant_score`  
    `$!constant_score`  
    `sort=constant_score`  
    `sort<constant_score`  
    `disp=constant_score`  
    `constant_score=2.5`  
    `constant_score!=2.5`  
    `constant_score>2.5`

### auto_score

!!! abstract "Aliases"
    autoscore, auto_score_up, autoscoreup, auto_up, auto_boost, auto_support, autoboost, autosupport, autoup

!!! info "Type"
    [Flag](/commands/general-usage/#flag), [Sortable](/commands/general-usage/#sortable), [Display](/commands/general-usage/#display), [Comparable](/commands/general-usage/#comparable)

!!! note "Tags"
    auto_score, autoscore, auto_score_up, autoscoreup, auto_up, auto_boost, auto_support, autoboost, autosupport, autoup

??? example "Examples"
    `$auto_score`  
    `$!auto_score`  
    `sort=auto_score`  
    `sort<auto_score`  
    `disp=auto_score`  
    `auto_score=2.5`  
    `auto_score!=2.5`  
    `auto_score>2.5`