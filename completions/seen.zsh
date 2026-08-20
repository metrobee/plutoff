#compdef seen plutoff

_seen() {
    local -a sub_opts tyyp_opts ohtrus_opts flags

    sub_opts=(
        'kuusk:Picea abies (Harilik kuusk)'
        'mänd:Pinus sylvestris (Harilik mänd)'
        'kask:Betula pendula (Arukask)'
        'sookask:Betula pubescens (Sookask)'
        'haab:Populus tremula (Harilik haab)'
        'lepp:Alnus incana (Hall lepp)'
        'sanglepp:Alnus glutinosa (Sanglepp / must lepp)'
        'tamm:Quercus robur (Harilik tamm)'
        'saar:Fraxinus excelsior (Harilik saar)'
        'vaher:Acer platanoides (Harilik vaher)'
        'sarapuu:Corylus avellana (Harilik sarapuu)'
        'pärn:Tilia cordata (Harilik pärn)'
    )

    tyyp_opts=(
        'lamatüvi:Mahakukkunud tüvi / lamapuu (Log)'
        'känd:Puukänd (Stump)'
        'tüügas:Püstine kuivanud tüvi (Snag)'
        'lamaoks:Mahakukkunud lamaoks'
        'elavpuu:Elav kasvav puu'
        'kõdupuit:Tugevasti kõdunenud puit'
        'kõdu:Metsakõdu / varis (Litter)'
        'okkad:Okkavaris'
        'lehed:Lehevaris'
        'muld:Metsamuld / mineraalpinnas'
    )

    ohtrus_opts=(
        'üksikud:Üksikud viljakehad (1-3 tk)'
        'vähe:Vähe (mõned eksemplarid)'
        'mõõdukalt:Mõõdukalt (tavaline leiukoht)'
        'sage:Sage (arvukalt viljakehi)'
        'palju:Palju (suurem kogumik)'
        'massiliselt:Massiliselt (ulatuslik esinemine)'
    )

    if [[ "$PREFIX" == sub:* ]]; then
        _describe -t sub_opts 'Substraadi puuliik' sub_opts -P "sub:"
        return 0
    fi

    if [[ "$PREFIX" == (tyyp|tüüp):* ]]; then
        local pfx="${PREFIX%%:*}:"
        _describe -t tyyp_opts 'Substraadi tüüp' tyyp_opts -P "$pfx"
        return 0
    fi

    if [[ "$PREFIX" == (ohtrus|oht):* ]]; then
        local pfx="${PREFIX%%:*}:"
        _describe -t ohtrus_opts 'Viljakehade ohtrus' ohtrus_opts -P "$pfx"
        return 0
    fi

    _arguments \
        '--help[Kuva abitekst]' \
        '--list[Kuva salvestatud vaatlused]' \
        '--sync[Sünkrooni PlutoF vaatlused kohalikku baasi]' \
        '--force[Luba teadlikult topeltfoto saatmine]' \
        '--keep[Jäta pildifailid alles]' \
        '*:fail:_files'
}

_seen "$@"
