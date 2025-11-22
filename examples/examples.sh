#!/bin/bash
export PYTHONPATH=../src
export DYLD_LIBRARY_PATH=/opt/homebrew/lib
#
# ISS (ZARYA)
# 1 25544U 98067A   25324.86734766  .00014275  00000-0  26737-3 0  9990
# 2 25544  51.6324 250.7347 0003961 150.1460 209.9755 15.48935269539463
uv run python -m puncher --form svg --form png --out iss_tle_0 --cstring "ISS (ZARYA)" 
uv run python -m puncher --form svg --form png --out iss_tle_1 --cstring "1 25544U 98067A   25324.86734766  .00014275  00000-0  26737-3 0  9990" 
uv run python -m puncher --form svg --form png --out iss_tle_2 --cstring "2 25544  51.6324 250.7347 0003961 150.1460 209.9755 15.48935269539463" 
uv run python -m puncher --form svg --form png --out charset --testpattern +cellboundaries +punchboundaries +printpunch