<!-- Generated Document: Do not edit -->

# music_filter

## Commands

### song

*[Detail Command](/commands/general-usage/#detail-commands)*

### chart

*[Detail Command](/commands/general-usage/#detail-commands)*

!!! note "Tab Names"
    expert, hard, normal, easy, expt, norm, exp, hrd, nrm, esy, ex, hd, nm, es

### sections

*[Detail Command](/commands/general-usage/#detail-commands)*

!!! note "Tab Names"
    expert, hard, normal, easy, expt, norm, exp, hrd, nrm, esy, ex, hd, nm, es

### songs

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
    [Sortable (Default)](/commands/general-usage/#sortable), [Display](/commands/general-usage/#display), [Comparable](/commands/general-usage/#comparable)

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
    `unit=その他`  
    `unit=happy_around!,unichørd,call_of_artemis`  
    `unit!=happy_around!,unichørd,call_of_artemis`  
    `$happy_around! $unichørd $call_of_artemis`  
    `$!その他 $!photon_maiden`

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
    [Sortable](/commands/general-usage/#sortable), [Display](/commands/general-usage/#display), [Equality](/commands/general-usage/#equality), [Plural](/commands/general-usage/#plural)

??? example "Examples"
    `sort=chart_designer`  
    `sort<chart_designer`  
    `disp=chart_designer`  
    `chart_designer=[value]`  
    `chart_designer!=[value]`

### level

!!! info "Type"
    [Sortable](/commands/general-usage/#sortable), [Display (Default)](/commands/general-usage/#display), [Comparable](/commands/general-usage/#comparable)

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
    [Sortable](/commands/general-usage/#sortable), [Display](/commands/general-usage/#display), [Comparable](/commands/general-usage/#comparable)

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
    [Sortable](/commands/general-usage/#sortable), [Display](/commands/general-usage/#display), [Comparable](/commands/general-usage/#comparable)

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
    [Sortable](/commands/general-usage/#sortable), [Display](/commands/general-usage/#display), [Comparable](/commands/general-usage/#comparable)

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
    [Sortable](/commands/general-usage/#sortable), [Display](/commands/general-usage/#display), [Comparable](/commands/general-usage/#comparable)

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

### expiring

!!! info "Type"
    [Flag](/commands/general-usage/#flag)

!!! note "Tags"
    expiring

??? example "Examples"
    `$expiring`  
    `$!expiring`