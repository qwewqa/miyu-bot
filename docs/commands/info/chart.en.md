<!-- Generated Document: Do not edit -->

# chart_filter

## Commands

### charts

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
    [Sortable](/commands/general-usage/#sortable), [Display](/commands/general-usage/#display), [Comparable](/commands/general-usage/#comparable)

??? example "Examples"
    `sort=date`  
    `sort<date`  
    `disp=date`  
    `date=[value]`  
    `date!=[value]`  
    `date>[value]`

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

??? example "Examples"
    `sort=unit`  
    `sort<unit`  
    `unit=スペシャル`  
    `unit=その他,lyrical_lily,photon_maiden`  
    `unit!=その他,lyrical_lily,photon_maiden`  
    `$その他 $lyrical_lily $photon_maiden`  
    `$!スペシャル $!燐舞曲`

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

### chart_designer

!!! abstract "Aliases"
    chartdesigner, designer

!!! info "Type"
    [Sortable](/commands/general-usage/#sortable), [Display](/commands/general-usage/#display), [Equality](/commands/general-usage/#equality)

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
    [Sortable](/commands/general-usage/#sortable), [Comparable](/commands/general-usage/#comparable), [Tag](/commands/general-usage/#tag), [Keyword](/commands/general-usage/#keyword)

??? note "Tags"
     - expert, expt  
     - hard  
     - normal, norm  
     - easy

??? example "Examples"
    `sort=difficulty`  
    `sort<difficulty`  
    `difficulty=normal`  
    `difficulty=easy,normal,expert`  
    `difficulty!=easy,normal,expert`  
    `difficulty>hard`  
    `$easy $normal $expert`  
    `$!normal $!hard`  
    `easy normal expert`

### level

!!! info "Type"
    [Sortable (Default)](/commands/general-usage/#sortable), [Comparable](/commands/general-usage/#comparable)

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
    [Sortable](/commands/general-usage/#sortable), [Display](/commands/general-usage/#display), [Comparable](/commands/general-usage/#comparable)

??? example "Examples"
    `sort=duration`  
    `sort<duration`  
    `disp=duration`  
    `duration=[value]`  
    `duration!=[value]`  
    `duration>[value]`

### bpm

!!! info "Type"
    [Sortable](/commands/general-usage/#sortable), [Display](/commands/general-usage/#display), [Comparable](/commands/general-usage/#comparable)

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
    [Sortable](/commands/general-usage/#sortable), [Display](/commands/general-usage/#display), [Comparable](/commands/general-usage/#comparable)

??? example "Examples"
    `sort=combo`  
    `sort<combo`  
    `disp=combo`  
    `combo=[value]`  
    `combo!=[value]`  
    `combo>[value]`

### playable

!!! info "Type"
    [Flag](/commands/general-usage/#flag)

!!! note "Tags"
    playable

??? example "Examples"
    `$playable`  
    `$!playable`

### score[skill%(*duration)?](groovy[bonus%])?

!!! info "Type"
    [Sortable](/commands/general-usage/#sortable), [Display](/commands/general-usage/#display)

??? example "Examples"
    `sort=score[skill%(*duration)?](groovy[bonus%])?`  
    `sort<score[skill%(*duration)?](groovy[bonus%])?`  
    `disp=score[skill%(*duration)?](groovy[bonus%])?`  
    `sort=score50`  
    `sort<score50`  
    `disp=score50`

### score[skill%(*duration)]solo

!!! info "Type"
    [Sortable](/commands/general-usage/#sortable), [Display](/commands/general-usage/#display)

??? example "Examples"
    `sort=score[skill%(*duration)]solo`  
    `sort<score[skill%(*duration)]solo`  
    `disp=score[skill%(*duration)]solo`  
    `sort=score50solo`  
    `sort<score50solo`  
    `disp=score50solo`