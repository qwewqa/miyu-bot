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

### 
