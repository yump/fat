#!/usr/bin/gnuplot
# Copyright (C) 2016 Russell Haley
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

datafile = "fat.dat"

set title "Eaten"
set key autotitle columnhead noenhanced

set xdata time
set timefmt "%s"
set format x "%Y/%m/%d"

set yrange [0:*]
plot datafile using 1:2 with linespoints
pause mouse

ncols = system("awk 'NR==1 {print NF}' ".datafile) + 0
print ncols
plot \
  for [i=3:ncols] \
    datafile using 1:(sum [col=i:ncols] column(col)) \
      title columnheader(i) \
      with filledcurves x1

pause mouse

plot for [i=3:ncols] datafile using 1:i with linespoints

pause mouse close
