#!/bin/bash
# Pre-script: stage the TACC-compiled OpenSeesPy next to the sweep tasks.
# EXTRA_MODULES=opensees,hdf5/1.14.4 provides TACC_OPENSEES_BIN and the runtime
# libraries. The bundled filename differs across opensees module versions
# (3.8.0 ships bin/opensees.so; older versions shipped bin/OpenSeesPy.so).
for f in "${TACC_OPENSEES_BIN}/opensees.so" "${TACC_OPENSEES_BIN}/OpenSeesPy.so"; do
    if [[ -f "$f" ]]; then
        cp "$f" ./opensees.so
        echo "Staged TACC OpenSeesPy: $f -> ./opensees.so"
        exit 0
    fi
done
echo "ERROR: no OpenSeesPy library found in ${TACC_OPENSEES_BIN}" >&2
exit 1
