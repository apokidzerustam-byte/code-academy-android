# Текст в терминале

```bash
printf "яблоко\nбанан\nвишня\nбанан\nапельсин\n" > fruits.txt
head -n 2 fruits.txt          # первые 2 строки
tail -n 1 fruits.txt          # последняя строка
wc -l fruits.txt              # число строк
grep банан fruits.txt         # строки со словом
grep -c банан fruits.txt      # сколько таких строк
sort fruits.txt | uniq        # уникальные, по алфавиту
sort fruits.txt | uniq | wc -l
```

`uniq` убирает только **соседние** одинаковые строки — сначала `sort`.
