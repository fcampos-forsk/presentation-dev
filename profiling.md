```
██████╗ ██████╗  ██████╗ ███████╗██╗██╗     ██╗███╗   ██╗ ██████╗ 
██╔══██╗██╔══██╗██╔═══██╗██╔════╝██║██║     ██║████╗  ██║██╔════╝ 
██████╔╝██████╔╝██║   ██║█████╗  ██║██║     ██║██╔██╗ ██║██║  ███╗
██╔═══╝ ██╔══██╗██║   ██║██╔══╝  ██║██║     ██║██║╚██╗██║██║   ██║
██║     ██║  ██║╚██████╔╝██║     ██║███████╗██║██║ ╚████║╚██████╔╝
╚═╝     ╚═╝  ╚═╝ ╚═════╝ ╚═╝     ╚═╝╚══════╝╚═╝╚═╝  ╚═══╝ ╚═════╝ 
                                                                  
```

réparti entre 2 modules: pstats et cProfile

https://docs.python.org/3/library/profile.html

## Utilisation de cProfile

Pour générer les dumps

```shell
python -m cProfile -o prof.dump -m gateway
```

## Utilisation de pstats

Pour explorer les stats

```python
from pstats import Stats, SortKey

s = Stats("prof.dump")
s.sort_stats(SortKey.TIME, SortKey.CALLS).print_stats("/gateway", .10)
```

## Avec outillage du code

voir https://docs.python.org/3/library/profile.html#profile.Profile

OU en utilisant profileit.py

## Visualisation avec snakeviz

```shell
uv tool install snakeviz
snakeviz -s prof.dump  # ou un dossier contenant des .dump
```

## packet capture

```shell
sudo nsenter -n -t $(docker inspect --format "{{ .State.Pid }}" devenv-mongodb-1) timeout 10 tcpdump -w out.pcap
```

> docker inspect --format "{{ .State.Pid }}" devenv-mongodb-1 := get container PID
> nsenter := namespace enter
> timeout 10 := kill after 10 sec
> tcpdump := packet capture...