<!-- Generated Document: Do not edit -->

# music_filter

## Commands

### song

*[Detail Command](../general_usage/#detail-commands)*

### chart

*[Detail Command](../general_usage/#detail-commands)*

!!! note "Tab Names"
    expert, hard, normal, easy, expt, norm, exp, hrd, nrm, esy, ex, hd, nm, es

### sections

*[Detail Command](../general_usage/#detail-commands)*

!!! note "Tab Names"
    expert, hard, normal, easy, expt, norm, exp, hrd, nrm, esy, ex, hd, nm, es

### songs

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
    [Sortable (Default)](../general_usage/#sortable), [Display](../general_usage/#display), [Comparable](../general_usage/#comparable)

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
    `unit=燐舞曲`  
    `unit=lyrical_lily,燐舞曲,その他`  
    `unit!=lyrical_lily,燐舞曲,その他`  
    `$lyrical_lily $燐舞曲 $その他`  
    `$!燐舞曲 $!lyrical_lily`

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
    [Sortable](../general_usage/#sortable), [Display](../general_usage/#display), [Equality](../general_usage/#equality), [Plural](../general_usage/#plural)

??? example "Examples"
    `sort=chart_designer`  
    `sort<chart_designer`  
    `disp=chart_designer`  
    `chart_designer=[value]`  
    `chart_designer!=[value]`

### level

!!! info "Type"
    [Sortable](../general_usage/#sortable), [Display (Default)](../general_usage/#display), [Comparable](../general_usage/#comparable)

??? example "Examples"
    `sort=level`  
    `sort<level`  
    `disp=level`  
    `level=[value]`  
    `level!=[value]`  
    `level>[value]`

### expert

!!! abstract "Aliases"
    exp, ex

!!! info "Type"
    [Sortable](../general_usage/#sortable), [Display](../general_usage/#display), [Comparable](../general_usage/#comparable)

??? example "Examples"
    `sort=expert`  
    `sort<expert`  
    `disp=expert`  
    `expert=[value]`  
    `expert!=[value]`  
    `expert>[value]`

### hard

!!! abstract "Aliases"
    hrd, hd

!!! info "Type"
    [Sortable](../general_usage/#sortable), [Display](../general_usage/#display), [Comparable](../general_usage/#comparable)

??? example "Examples"
    `sort=hard`  
    `sort<hard`  
    `disp=hard`  
    `hard=[value]`  
    `hard!=[value]`  
    `hard>[value]`

### normal

!!! abstract "Aliases"
    norm, nrm, nm

!!! info "Type"
    [Sortable](../general_usage/#sortable), [Display](../general_usage/#display), [Comparable](../general_usage/#comparable)

??? example "Examples"
    `sort=normal`  
    `sort<normal`  
    `disp=normal`  
    `normal=[value]`  
    `normal!=[value]`  
    `normal>[value]`

### easy

!!! abstract "Aliases"
    esy, es

!!! info "Type"
    [Sortable](../general_usage/#sortable), [Display](../general_usage/#display), [Comparable](../general_usage/#comparable)

??? example "Examples"
    `sort=easy`  
    `sort<easy`  
    `disp=easy`  
    `easy=[value]`  
    `easy!=[value]`  
    `easy>[value]`

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