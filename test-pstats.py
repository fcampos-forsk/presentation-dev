import pstats

p = pstats.Stats('prof.dump')
p.print_stats()
