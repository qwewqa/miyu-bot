<!-- Generated Document: Do not edit -->

# chart_filter

## Commands

### charts

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
    [Sortable](../general_usage/#sortable), [Display](../general_usage/#display), [Comparable](../general_usage/#comparable)

??? example "Examples"
    `sort=date`  
    `sort<date`  
    `disp=date`  
    `date=[value]`  
    `date!=[value]`  
    `date>[value]`

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

??? example "Examples"
    `sort=unit`  
    `sort<unit`  
    `unit=lyrical_lily`  
    `unit=merm4id,peaky_p-key,lyrical_lily`  
    `unit!=merm4id,peaky_p-key,lyrical_lily`  
    `$merm4id $peaky_p-key $lyrical_lily`  
    `$!lyrical_lily $!peaky_p-key`

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

### chart_designer

!!! abstract "Aliases"
    chartdesigner, designer

!!! info "Type"
    [Sortable](../general_usage/#sortable), [Display](../general_usage/#display), [Equality](../general_usage/#equality)

??? example "Examples"
    `sort=chart_designer`  
    `sort<chart_designer`  
    `disp=chart_designer`  
    `chart_designer=[value]`  
    `chart_designer!=[value]`

### difficulty

!!! abstract "Aliases"
    diff

!!! info "Type"
    [Sortable](../general_usage/#sortable), [Comparable](../general_usage/#comparable), [Tag](../general_usage/#tag), [Keyword](../general_usage/#keyword)

??? note "Tags"
     - expert, expt  
     - hard  
     - normal, norm  
     - easy

??? example "Examples"
    `sort=difficulty`  
    `sort<difficulty`  
    `difficulty=easy`  
    `difficulty=easy,expert,hard`  
    `difficulty!=easy,expert,hard`  
    `difficulty>hard`  
    `$easy $expert $hard`  
    `$!easy $!hard`  
    `easy expert hard`

### level

!!! info "Type"
    [Sortable (Default)](../general_usage/#sortable), [Comparable](../general_usage/#comparable)

??? example "Examples"
    `sort=level`  
    `sort<level`  
    `level=[value]`  
    `level!=[value]`  
    `level>[value]`

### duration

!!! abstract "Aliases"
    length

!!! info "Type"
    [Sortable](../general_usage/#sortable), [Display](../general_usage/#display), [Comparable](../general_usage/#comparable)

??? example "Examples"
    `sort=duration`  
    `sort<duration`  
    `disp=duration`  
    `duration=[value]`  
    `duration!=[value]`  
    `duration>[value]`

### bpm

!!! info "Type"
    [Sortable](../general_usage/#sortable), [Display](../general_usage/#display), [Comparable](../general_usage/#comparable)

??? example "Examples"
    `sort=bpm`  
    `sort<bpm`  
    `disp=bpm`  
    `bpm=[value]`  
    `bpm!=[value]`  
    `bpm>[value]`

### combo

!!! abstract "Aliases"
    max_combo, maxcombo

!!! info "Type"
    [Sortable](../general_usage/#sortable), [Display](../general_usage/#display), [Comparable](../general_usage/#comparable)

??? example "Examples"
    `sort=combo`  
    `sort<combo`  
    `disp=combo`  
    `combo=[value]`  
    `combo!=[value]`  
    `combo>[value]`

### playable

!!! info "Type"
    [Flag](../general_usage/#flag)

!!! note "Tags"
    playable

??? example "Examples"
    `$playable`  
    `$!playable`

### score[skill%]

!!! info "Type"
    [Sortable](../general_usage/#sortable), [Display](../general_usage/#display)

??? example "Examples"
    `sort=score[skill%]`  
    `sort<score[skill%]`  
    `disp=score[skill%]`  
    `sort=score50`  
    `sort<score50`  
    `disp=score50`

### score[skill%]solo

!!! info "Type"
    [Sortable](../general_usage/#sortable), [Display](../general_usage/#display)

??? example "Examples"
    `sort=score[skill%]solo`  
    `sort<score[skill%]solo`  
    `disp=score[skill%]solo`  
    `sort=score50solo`  
    `sort<score50solo`  
    `disp=score50solo`