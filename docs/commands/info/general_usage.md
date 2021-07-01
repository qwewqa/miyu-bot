# General Usage

Commands in the *Info* section support special argument types
to allow for specific filtering and display options of search results.

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

!!! danger
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
