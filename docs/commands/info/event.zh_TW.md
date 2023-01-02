<!-- Generated Document: Do not edit -->

# event_filter

## Commands

### event

*[Detail Command](/commands/general-usage/#detail-commands)*

### events

*[List Command](/commands/general-usage/#list-commands)*

## Attributes

### date

!!! abstract "Aliases"
    release, recent

!!! info "Type"
    [Sortable (Default)](/commands/general-usage/#sortable), [Display (Default)](/commands/general-usage/#display), [Comparable](/commands/general-usage/#comparable)

??? example "Examples"
    `sort=date`  
    `sort<date`  
    `disp=date`  
    `date=[value]`  
    `date!=[value]`  
    `date>[value]`

### character

!!! abstract "Aliases"
    char, chara

!!! info "Type"
    [Equality](/commands/general-usage/#equality), [Tag](/commands/general-usage/#tag), [Plural](/commands/general-usage/#plural)

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
    `character=esora`  
    `character=haruna,rika,dalia`  
    `character!=haruna,rika,dalia`  
    `character==haruna,rika,dalia`  
    `$haruna $rika $dalia`  
    `$!esora $!hayate`

### unit

!!! info "Type"
    [Sortable](/commands/general-usage/#sortable), [Equality](/commands/general-usage/#equality), [Tag](/commands/general-usage/#tag)

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
     - mixed

??? example "Examples"
    `sort=unit`  
    `sort<unit`  
    `unit=happy_around!`  
    `unit=peaky_p-key,merm4id,lyrical_lily`  
    `unit!=peaky_p-key,merm4id,lyrical_lily`  
    `$peaky_p-key $merm4id $lyrical_lily`  
    `$!happy_around! $!燐舞曲`

### attribute

!!! info "Type"
    [Sortable](/commands/general-usage/#sortable), [Equality](/commands/general-usage/#equality), [Tag](/commands/general-usage/#tag)

??? note "Tags"
     - street, purple  
     - party, yellow, orange  
     - cute, pink, red  
     - cool, blue  
     - elegant, green

??? example "Examples"
    `sort=attribute`  
    `sort<attribute`  
    `attribute=party`  
    `attribute=cool,street,elegant`  
    `attribute!=cool,street,elegant`  
    `$cool $street $elegant`  
    `$!party $!cute`

### type

!!! info "Type"
    [Sortable](/commands/general-usage/#sortable), [Display](/commands/general-usage/#display), [Equality](/commands/general-usage/#equality), [Tag](/commands/general-usage/#tag)

??? note "Tags"
     - nothing  
     - bingo  
     - medley  
     - poker  
     - raid  
     - slot

??? example "Examples"
    `sort=type`  
    `sort<type`  
    `disp=type`  
    `type=bingo`  
    `type=nothing,raid,slot`  
    `type!=nothing,raid,slot`  
    `$nothing $raid $slot`  
    `$!bingo $!slot`

### parameter

!!! abstract "Aliases"
    param

!!! info "Type"
    [Sortable](/commands/general-usage/#sortable), [Equality](/commands/general-usage/#equality), [Tag](/commands/general-usage/#tag)

??? note "Tags"
     - heart  
     - technique, tech  
     - physical, phys  
     - no_parameter, noparameter

??? example "Examples"
    `sort=parameter`  
    `sort<parameter`  
    `parameter=heart`  
    `parameter=technique,physical,heart`  
    `parameter!=technique,physical,heart`  
    `$technique $physical $heart`  
    `$!heart $!no_parameter`