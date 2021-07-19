# General Usage
Commands fit broadly into two categories: *Info* and *Utility*.

Commands in the *Utility* category vary in usage, and details can be found in a per-command basis.

Commands in the *Info* category are organized into groups, which each have their own set
of accepted arguments which fall under the below types.

## Argument Types

### Named Arguments
Named arguments have a name, operator, and value.
```
!banners disp=id
!cards power>34000
!songs bpm<=160
```

!!! warning
    Values with spaces in them must be quoted.
    !!! failure "Wrong"
        ```
        !chart designer=MU & Subatos
        ```
    !!! success "Correct"
        ```
        !chart designer="MU & Subatos"
        ```

Some named arguments allow for multiple argument values.
```
!cards attribute=elegant,cool
```

!!! warning
    Spaces are not allowed before or after commas in argument lists.
    !!! failure "Wrong"
        ```
        !songs unit=hapiara, pkpk
        ```
    !!! success "Correct"
        ```
        !songs unit=hapiara,pkpk
        ```

Some named arguments can be repeated.
```
!songs bpm>140 bpm<=160
```

### Tags
Tags start with a `$` sign.
```
!songs $lili
!events $rinku $kyoko
```
Some tags can be inverted, excluding results matching them.
```
!songs $!other $!special
```
Invalid tags will cause an error to be returned.

### Keywords
Keyword are like tags, but they do not require a `$` sign.  
Keywords are used less frequently than tags because there is potential
for keywords to be unintentionally used, and because invalid keywords are not detected.
```
!cards noa saki
```
Like other types of arguments, the location of a keyword does not matter.
```
!card poison esora
!card esora poison
```
Many keywords have tag counterparts, allowing them to be used in either fashion.
```
!cards $noa $saki
```

### Text Argument
Anything not falling into any of the above argument types is combined and processed as the text argument.
The text argument, if present, is used to find search results by name. It allows for shortened or abbreviated names, and can tolerate some errors.
```
!song discover universe
!song du
!song discover
!song diiscover umiverse
```

If the text argument is `~n` where n is a number, it will skip to the nth result.
```
# Goes to the page with the 20th result
!cards $elegant ~20

# Brings up the 20th result
!card $elegant ~20
```

## Command Groups
Commands in the Info category are divided into groups.
For example, the `!song`, `!songs`, and `!chart` commands are all part of the [Music](../music/) group.
Commands in the same group share a common set of [attributes](#attributes) which determine
what arguments are available.

## Command Group Attributes
Attributes vary in how they are used based on their type.
An attribute can have multiple types such that it can be used in multiple ways.

Some attributes have aliases, which allow them to be referenced using a different name.

### Sortable
Sortable attributes are valid values for the `sort` argument.
```
!cards sort=power
```

### Display
Display attributes are valid values for the `disp` argument in [list commands](#list-commands).
The `disp` argument for [detail commands](#detail-commands) has no effect.
```
!songs disp=bpm
```

### Tag
Tag arguments have tags that can be used. See [tags](#tags).

### Keyword
Keyword arguments have keywords, which usually also appear as tags. See [keywords](#keywords).

### Equality
Equality attributes can be used as named arguments with the `=` and `!=` operators.
```
!cards unit=pkpk
!cards unit!=pkpk
```

### Comparable
Comparable attributes are like equality attributes, but also support `>`, `<`, `>=`, and `<=` as operators.
```
!song level=12+
!song level>=13
```

### Plural
Plural attributes are ones that can have multiple values for a single result.
The behavior of tags and equality is altered for plural attributes, and the `==` operator
is added for equality comparisons.
```
# Only events with both Noa and Saki.
!events $noa $saki
!events char==noa,saki

# Events with at least one of Noa or Saki.
!events char=noa,saki

# Events with neither Noa nor Saki.
!events char!=noa,saki
```

### Flag
Flag attributes have a single tag, which can be used like other tags.
Special flag attributes do not support an inverted (`$!`) tag.

## Command Types

### List Commands
List commands usually have a plural name such as `!songs` or `!cards`.
Using a list command brings up a list of results.

### Detail Commands
Detail commands usually have a singular name such as `!song` or `!card`.
Using a detail command brings up details on a single result at a time.

#### Tabs
Some detail arguments have tabs, which can be specified as the last word in the
text argument.
```
!chart synchro hard
!card shinobu untrained
```

## Common arguments
All *Info* commands share the following common arguments.

### Sort
Sets sort order. See [Sortable](#sortable).
```
!cards sort=power
```

### Display
Sets list display. See [Display](#display).
```
!songs disp=bpm
```

### Start
Sets the starting value, by name.
```
!song start=wondertrip
```
