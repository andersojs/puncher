#!/bin/bash
export DYLD_LIBRARY_PATH=/opt/homebrew/lib

# ISS (ZARYA)
# 1 25544U 98067A   25324.86734766  .00014275  00000-0  26737-3 0  9990
# 2 25544  51.6324 250.7347 0003961 150.1460 209.9755 15.48935269539463
TLE_STRING_0="ISS (ZARYA)"
TLE_STRING_1="1 25544U 98067A   25324.86734766  .00014275  00000-0  26737-3 0  9990"
TLE_STRING_2="2 25544  51.6324 250.7347 0003961 150.1460 209.9755 15.48935269539463" 

uv run puncher --form svg --form png --out iss_tle_0 --cstring "${TLE_STRING_0}"
uv run puncher --form svg --out iss_tle_0_flat +flatten --cstring "${TLE_STRING_0}"

uv run puncher --form svg --form png --out iss_tle_1 --cstring  "${TLE_STRING_1}"
uv run puncher --form svg --out iss_tle_1_flat +flatten --cstring  "${TLE_STRING_1}"

uv run puncher --form svg --form png --out iss_tle_2 --cstring  "${TLE_STRING_2}"
uv run puncher --form svg --out iss_tle_2_flat +flatten --cstring  "${TLE_STRING_2}"

uv run puncher --form svg --form png --out charset --testpattern +cellboundaries +punchboundaries +printpunch
uv run puncher --form svg --out charset_flat +flatten --testpattern +cellboundaries +punchboundaries +printpunch