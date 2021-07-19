<!-- Generated Document: Do not edit -->

# gacha_filter

## Commands

### banner

*[Detail Command](../general_usage/#detail-commands)*

### banner_rates

*[Detail Command](../general_usage/#detail-commands)*

### banners

*[List Command](../general_usage/#list-commands)*

## Attributes

### name

!!! abstract "Aliases"
    title

!!! info "Type"
    [Sortable](../general_usage/#sortable)

??? example "Examples"
    `sort=name`  
    `sort<name`

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
    `character=saki`  
    `character=muni,shinobu,pekora`  
    `character!=muni,shinobu,pekora`  
    `character==muni,shinobu,pekora`  
    `$muni $shinobu $pekora`  
    `$!saki $!ibuki`

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
    `unit=スペシャル`  
    `unit=mixed,merm4id,スペシャル`  
    `unit!=mixed,merm4id,スペシャル`  
    `$mixed $merm4id $スペシャル`  
    `$!スペシャル $!燐舞曲`

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
    `attribute=party`  
    `attribute=elegant,cute,party`  
    `attribute!=elegant,cute,party`  
    `$elegant $cute $party`  
    `$!party $!cool`

### id

!!! info "Type"
    [Sortable](../general_usage/#sortable), [Display](../general_usage/#display), [Comparable](../general_usage/#comparable)

??? example "Examples"
    `sort=id`  
    `sort<id`  
    `disp=id`  
    `id=[value]`  
    `id!=[value]`  
    `id>[value]`