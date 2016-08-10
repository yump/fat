#!/usr/bin/gnuplot

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
