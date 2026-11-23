# Операции с файлами

```bash
touch report.txt             # создать пустой файл
cp report.txt backup.txt     # копировать
mv backup.txt old.txt        # переименовать
mkdir archive
mv old.txt archive           # переместить в папку
rm report.txt                # удалить файл
rm -r archive                # удалить папку с содержимым
ls *.txt                     # маска: все .txt
```

> Корзины нет. Перед `rm` с маской проверьте её командой `ls`.
