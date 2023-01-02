<!-- Generated Document: Do not edit -->

# gacha_filter

## Commands

### banner

*[Detail Command](/commands/general-usage/#detail-commands)*

### banner_rates

*[Detail Command](/commands/general-usage/#detail-commands)*

### banners

*[List Command](/commands/general-usage/#list-commands)*

## Attributes

### name

!!! abstract "Aliases"
    title

!!! info "Type"
    [Sortable](/commands/general-usage/#sortable)

??? example "Examples"
    `sort=name`  
    `sort<name`

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
    `character=sophia`  
    `character=sophia,dalia,marika`  
    `character!=sophia,dalia,marika`  
    `character==sophia,dalia,marika`  
    `$sophia $dalia $marika`  
    `$!sophia $!nagisa`

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
    `unit=その他`  
    `unit=call_of_artemis,スペシャル,燐舞曲`  
    `unit!=call_of_artemis,スペシャル,燐舞曲`  
    `$call_of_artemis $スペシャル $燐舞曲`  
    `$!その他 $!スペシャル`

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
    `attribute=cool`  
    `attribute=cute,street,party`  
    `attribute!=cute,street,party`  
    `$cute $street $party`  
    `$!cool $!elegant`

### id

!!! info "Type"
    [Sortable](/commands/general-usage/#sortable), [Display](/commands/general-usage/#display), [Comparable](/commands/general-usage/#comparable)

??? example "Examples"
    `sort=id`  
    `sort<id`  
    `disp=id`  
    `id=[value]`  
    `id!=[value]`  
    `id>[value]`