# Ветки

```bash
git branch                 # список веток
git switch -c feature      # создать и перейти
git switch main            # вернуться
git merge feature          # слить feature в текущую ветку
git branch -d feature      # удалить слитую ветку
git log --oneline --graph --all
```

## Запомните

1. Сливают **в** текущую ветку: сначала `git switch main`, потом `git merge feature`.
2. Перемотка (fast-forward) возможна, если основная ветка не двигалась.
3. Одна задача — одна ветка.
