<!-- Generated Document: Do not edit -->

# Card

Card related commands.

## Commands

### card

*[Detail Command](../general_usage/#detail-commands)*

!!! note "Tab Names"
    untrained, trained

!!! question "Description"
    Card details.

### cards

*[List Command](../general_usage/#list-commands)*

!!! question "Description"
    Card list.

## Attributes

### name

!!! abstract "Aliases"
    title

!!! info "Type"
    [Sortable](../general_usage/#sortable)

!!! question "Description"
    Card name.

??? example "Examples"
    `sort=name`  
    `sort<name`

### character

!!! abstract "Aliases"
    char, chara

!!! info "Type"
    [Sortable](../general_usage/#sortable), [Equality](../general_usage/#equality), [Tag](../general_usage/#tag), [Keyword](../general_usage/#keyword)

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
     - syano  
     - touka  
     - michiru  
     - ryujin  
     - dennojo  
     - ku  
     - haruki  
     - aqua  
     - pekora  
     - fubuki  
     - suisei

??? example "Examples"
    `sort=character`  
    `sort<character`  
    `character=airi`  
    `character=muni,tsubaki,haruki`  
    `character!=muni,tsubaki,haruki`  
    `$muni $tsubaki $haruki`  
    `$!airi $!syano`  
    `muni tsubaki haruki`

### unit

!!! info "Type"
    [Sortable](../general_usage/#sortable), [Equality](../general_usage/#equality), [Tag](../general_usage/#tag)

!!! question "Description"
    Card character unit.

??? note "Tags"
     - happy_around!, happyaround, happy_around, hapiara, happy, ha  
     - peaky_p-key, peakyp-key, peakypkey, peaky, p-key, pkey, pkpk, pk  
     - photon_maiden, photonmaiden, photome, photon, pm  
     - merm4id, mermaid, mmd, m4  
     - 燐舞曲, rondo  
     - lyrical_lily, lyricallily, riririri, lililili, lily, lili, riri, ll  
     - スペシャル, special  
     - その他, other

??? example "Examples"
    `sort=unit`  
    `sort<unit`  
    `unit=その他`  
    `unit=燐舞曲,merm4id,photon_maiden`  
    `unit!=燐舞曲,merm4id,photon_maiden`  
    `$燐舞曲 $merm4id $photon_maiden`  
    `$!その他 $!merm4id`

### attribute

!!! info "Type"
    [Sortable](../general_usage/#sortable), [Equality](../general_usage/#equality), [Tag](../general_usage/#tag)

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
    [Sortable](../general_usage/#sortable), [Display](../general_usage/#display), [Comparable](../general_usage/#comparable)

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
    [Sortable](../general_usage/#sortable), [Display (Default)](../general_usage/#display), [Comparable](../general_usage/#comparable)

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
    [Sortable](../general_usage/#sortable), [Display](../general_usage/#display), [Comparable](../general_usage/#comparable)

!!! question "Description"
    Heart stat at max level.

??? example "Examples"
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
    [Sortable](../general_usage/#sortable), [Display](../general_usage/#display), [Comparable](../general_usage/#comparable)

!!! question "Description"
    Technique stat at max level.

??? example "Examples"
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
    [Sortable](../general_usage/#sortable), [Display](../general_usage/#display), [Comparable](../general_usage/#comparable)

!!! question "Description"
    Physical stat at max level.

??? example "Examples"
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
    [Sortable (Default)](../general_usage/#sortable), [Display](../general_usage/#display), [Comparable](../general_usage/#comparable)

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
    [Sortable](../general_usage/#sortable), [Keyword](../general_usage/#keyword)

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
    [Sortable](../general_usage/#sortable), [Display](../general_usage/#display), [Comparable](../general_usage/#comparable)

!!! question "Description"
    Card skill.

??? example "Examples"
    `sort=skill`  
    `sort<skill`  
    `disp=skill`  
    `skill=50`  
    `skill!=50`  
    `skill>50`

### event

!!! abstract "Aliases"
    event_bonus, eventbonus, bonus

!!! info "Type"
    [Special Flag](../general_usage/#flag), [Sortable](../general_usage/#sortable), [Comparable](../general_usage/#comparable)

!!! question "Description"
    Related event.

!!! note "Tags"
    event, event_bonus, eventbonus, bonus

??? example "Examples"
    `$event`  
    `sort=event`  
    `sort<event`  
    `event=[value]`  
    `event!=[value]`  
    `event>[value]`

### availability

!!! abstract "Aliases"
    avail

!!! info "Type"
    [Sortable](../general_usage/#sortable), [Display](../general_usage/#display), [Tag](../general_usage/#tag)

??? note "Tags"
     - unknown_availability, unavail, navl  
     - permanent, perm, prm  
     - limited, lmtd, lim  
     - collaboration, collab, cllb, clb  
     - birthday, bday  
     - welfare, free, reward, rwrd

??? example "Examples"
    `sort=availability`  
    `sort<availability`  
    `disp=availability`  
    `$welfare $unknown_availability $limited`  
    `$!limited $!unknown_availability`