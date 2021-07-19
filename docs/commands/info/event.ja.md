<!-- Generated Document: Do not edit -->

# event_filter

## Commands

### event

*[Detail Command](../general_usage/#detail-commands)*

### events

*[List Command](../general_usage/#list-commands)*

## Attributes

### date

!!! abstract "Aliases"
    release, recent

!!! info "Type"
    [Sortable (Default)](../general_usage/#sortable), [Display (Default)](../general_usage/#display), [Comparable](../general_usage/#comparable)

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
    [Equality](../general_usage/#equality), [Tag](../general_usage/#tag), [Plural](../general_usage/#plural)

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
    `character=haruna`  
    `character=rei,yuka,ibuki`  
    `character!=rei,yuka,ibuki`  
    `character==rei,yuka,ibuki`  
    `$rei $yuka $ibuki`  
    `$!haruna $!touka`

### unit

!!! info "Type"
    [Sortable](../general_usage/#sortable), [Equality](../general_usage/#equality), [Tag](../general_usage/#tag)

??? note "Tags"
     - happy_around!, happyaround, happy_around, hapiara, happy, ha  
     - peaky_p-key, peakyp-key, peakypkey, peaky, p-key, pkey, pkpk, pk  
     - photon_maiden, photonmaiden, photome, photon, pm  
     - merm4id, mermaid, mmd, m4  
     - 燐舞曲, rondo  
     - lyrical_lily, lyricallily, riririri, lililili, lily, lili, riri, ll  
     - スペシャル, special  
     - その他, other  
     - mixed

??? example "Examples"
    `sort=unit`  
    `sort<unit`  
    `unit=merm4id`  
    `unit=mixed,peaky_p-key,happy_around!`  
    `unit!=mixed,peaky_p-key,happy_around!`  
    `$mixed $peaky_p-key $happy_around!`  
    `$!merm4id $!happy_around!`

### attribute

!!! info "Type"
    [Sortable](../general_usage/#sortable), [Equality](../general_usage/#equality), [Tag](../general_usage/#tag)

??? note "Tags"
     - street, purple  
     - party, yellow, orange  
     - cute, pink, red  
     - cool, blue  
     - elegant, green

??? example "Examples"
    `sort=attribute`  
    `sort<attribute`  
    `attribute=street`  
    `attribute=elegant,street,party`  
    `attribute!=elegant,street,party`  
    `$elegant $street $party`  
    `$!street $!party`

### type

!!! info "Type"
    [Sortable](../general_usage/#sortable), [Display](../general_usage/#display), [Equality](../general_usage/#equality), [Tag](../general_usage/#tag)

??? note "Tags"
     - nothing  
     - bingo  
     - medley  
     - poker  
     - raid

??? example "Examples"
    `sort=type`  
    `sort<type`  
    `disp=type`  
    `type=nothing`  
    `type=nothing,raid,medley`  
    `type!=nothing,raid,medley`  
    `$nothing $raid $medley`  
    `$!nothing $!medley`

### parameter

!!! abstract "Aliases"
    param

!!! info "Type"
    [Sortable](../general_usage/#sortable), [Equality](../general_usage/#equality), [Tag](../general_usage/#tag)

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