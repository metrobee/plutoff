# Bash completion for seen / plutoff
_seen_bash() {
    local cur prev opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"

    if [[ "$cur" == sub:* ]]; then
        local prefix="sub:"
        local term="${cur#sub:}"
        local sub_opts="kuusk mänd kask sookask haab lepp sanglepp tamm saar vaher sarapuu pärn"
        COMPREPLY=( $(compgen -W "$sub_opts" -P "$prefix" -- "$term") )
        return 0
    fi

    if [[ "$cur" == tyyp:* || "$cur" == tüüp:* ]]; then
        local prefix="${cur%%:*}:"
        local term="${cur#*:}"
        local tyyp_opts="lamatüvi känd tüügas lamaoks elavpuu kõdupuit kõdu okkad lehed muld"
        COMPREPLY=( $(compgen -W "$tyyp_opts" -P "$prefix" -- "$term") )
        return 0
    fi

    if [[ "$cur" == ohtrus:* || "$cur" == oht:* ]]; then
        local prefix="${cur%%:*}:"
        local term="${cur#*:}"
        local oht_opts="üksikud vähe mõõdukalt sage palju massiliselt"
        COMPREPLY=( $(compgen -W "$oht_opts" -P "$prefix" -- "$term") )
        return 0
    fi

    local basic_opts="sub: tyyp: tüüp: ohtrus: märkus: --help --list --sync --auth-google --force --keep"
    COMPREPLY=( $(compgen -W "$basic_opts" -- "$cur") )
}
complete -o nospace -F _seen_bash seen plutoff
